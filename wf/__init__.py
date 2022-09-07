import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from dataclasses_json import dataclass_json
from flytekit import task
from flytekitplugins.pod import Pod
from kubernetes.client.models import (
    V1Container,
    V1PodSpec,
    V1ResourceRequirements,
    V1Toleration,
)
from latch import map_task, message, small_task, workflow
from latch.resources.launch_plan import LaunchPlan
from latch.types import LatchFile

from .docs import metadata


@dataclass_json
@dataclass
class Sample:
    name: str
    fasta: LatchFile


# From: https://github.com/latch-verified/bulk-rnaseq/blob/64a25531e1ddc43be0afffbde91af03754fb7c8c/wf/__init__.py
def _get_96_spot_pod() -> Pod:
    """[ "c6i.24xlarge", "c5.24xlarge", "c5.metal", "c5d.24xlarge", "c5d.metal" ]"""

    primary_container = V1Container(name="primary")
    resources = V1ResourceRequirements(
        requests={"cpu": "90", "memory": "170Gi"},
        limits={"cpu": "96", "memory": "192Gi"},
    )
    primary_container.resources = resources

    return Pod(
        pod_spec=V1PodSpec(
            containers=[primary_container],
            tolerations=[
                V1Toleration(effect="NoSchedule", key="ng", value="cpu-96-spot")
            ],
        ),
        primary_container_name="primary",
    )


large_spot_task = task(task_config=_get_96_spot_pod(), retries=3)


def _capture_output(command: List[str]) -> Tuple[int, str]:
    captured_stdout = []

    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
    ) as process:
        assert process.stdout is not None
        for line in process.stdout:
            print(line)
            captured_stdout.append(line)
        process.wait()
        returncode = process.returncode

    return returncode, "\n".join(captured_stdout)


@large_spot_task
def pangolin(
    sample: Sample,
) -> LatchFile:

    output_filename = f"{sample.name}_lineage_report.csv"
    remote_path = f"latch:///pangolin_outputs/{output_filename}"
    output_file = Path(output_filename).resolve()

    _pangolin_cmd = [
        "/root/pangolin",
        sample.fasta.local_path,
        "--outfile",
        output_filename,
    ]

    return_code, stdout = _capture_output(_pangolin_cmd)

    running_cmd = " ".join(_pangolin_cmd)

    message(
        "info",
        {
            "title": f"Executing Pangolin",
            "body": running_cmd,
        },
    )

    if return_code != 0:
        errors = re.findall("Exception.*", stdout[1])
        for error in errors:
            message(
                "error",
                {
                    "title": f"An error was raised while running pangolin for {sample.name}:",
                    "body": error,
                },
            )
        raise RuntimeError

    return LatchFile(str(output_file), remote_path)


@small_task
def multiqc(samples: List[LatchFile]) -> LatchFile:

    files = [sample.local_path for sample in samples]

    output_filename = "pangolin_multiqc_report.html"
    output_file = Path(output_filename).resolve()

    _multiqc_cmd = ["/root/multiqc"]

    _multiqc_cmd.extend(files)

    _multiqc_cmd.extend(["-n", output_file])

    subprocess.run(_multiqc_cmd)

    return LatchFile(str(output_file), f"latch:///{output_filename}")


@workflow(metadata)
def pangolin(samples: List[Sample]) -> LatchFile:
    """Phylogenetic Assignment of Named Global Outbreak LINeages

    Pangolin
    ---
    """
    outputs = map_task(pangolin)(sample=samples)
    return multiqc(samples=outputs)


LaunchPlan(
    pangolin,
    "FASTA files with viral contigs",
    {
        "samples": [
            Sample(
                name="viral_one",
                fasta=LatchFile("s3://latch-public/test-data/4318/cluster_cov.fasta"),
            )
        ]
    },
)
