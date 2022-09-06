from latch.types import LatchAuthor, LatchMetadata, LatchParameter

metadata = LatchMetadata(
    display_name="Pangolin",
    documentation="https://github.com/jvfe/pangolin_latch/blob/main/README.md",
    author=LatchAuthor(
        name="jvfe",
        github="https://github.com/jvfe",
    ),
    repository="https://github.com/jvfe/pangolin_latch",
    license="MIT",
    tags=["NGS", "virus", "lineage"],
)

metadata.parameters = {
    "samples": LatchParameter(
        display_name="Pangolin samples (FASTA files)",
        description="FASTA files with viral sequences.",
        batch_table_column=True,
        section_title="Data",
    ),
}
