import os
from dnaweaver import (
    CommercialDnaOffer,
    DnaAssemblyStation,
    GibsonAssemblyMethod,
    GoldenGateAssemblyMethod,
    BuildAGenomeAssemblyMethod,
    DnaSuppliersComparator,
    TmSegmentSelector,
    FixedSizeSegmentSelector,
    SequenceLengthConstraint,
    NoPatternConstraint
) 
from dnaweaver.reports import write_full_report



# OLIGO COMPANIES

cheap_dna_com = CommercialDnaOffer(
    name="CheapDNA.com",
    sequence_constraints=[NoPatternConstraint("GGTCTC"),
                          lambda seq: len(seq) < 200],
    pricing=lambda sequence: 0.10 * len(sequence),
    lead_time=10,
    memoize=True
)

deluxe_dna_com = CommercialDnaOffer(
    name="DeluxeDNA.com",
    sequence_constraints=[lambda seq: len(seq) < 200],
    pricing=lambda sequence: 0.20 * len(sequence),
    lead_time=5,
    memoize=True
)

big_dna_com = CommercialDnaOffer(
    name="BigDNA.com",
    sequence_constraints=[SequenceLengthConstraint(min_length=2000,
                                                   max_length=4000)],
    pricing=lambda sequence: 0.40 * len(sequence),
    lead_time=10,
    memoize=True
)

# OLIGOS TO BLOCKS ASSEMBLY

oligo_assembly_station = DnaAssemblyStation(
    name="Oligo Assembly Station",
    assembly_method=BuildAGenomeAssemblyMethod(
        overhang_selector=TmSegmentSelector(),
        min_segment_length=40,
        max_segment_length=100,
        duration=8,
        cost=0
    ),
    supplier=DnaSuppliersComparator([
        cheap_dna_com,
        deluxe_dna_com
    ]),
    coarse_grain=10,
    fine_grain=2,
    memoize=True,
)


# BLOCKS TO CHUNKS ASSEMBLY

blocks_sources_comparator = DnaSuppliersComparator(
    [
        oligo_assembly_station,
        big_dna_com
    ],
    memoize=True
)


blocks_assembly_comparator = DnaSuppliersComparator([
    DnaAssemblyStation(
        name="Blocks Assembly (Gibson)",
        assembly_method=GibsonAssemblyMethod(
            overhang_selector=TmSegmentSelector(min_size=15, max_size=30),
            min_segment_length=2000,
            max_segment_length=4000,
            duration=8,
            cost=10
        ),
        supplier=blocks_sources_comparator,
        coarse_grain=300,
        fine_grain=False,
        memoize=True
    ),
    DnaAssemblyStation(
        name="Blocks Assembly (Golden Gate)",
        assembly_method=GoldenGateAssemblyMethod(
            enzyme='BsaI',
            min_segment_length=2000,
            max_segment_length=4000,
            duration=5,
            cost=2
        ),
        supplier=blocks_sources_comparator,
        coarse_grain=300,
        fine_grain=30,
        memoize=True
    )
])


# CHUNKS TO MEGACHUNKS ASSEMBLY

chunks_assembly_station = DnaAssemblyStation(
    name="Yeast Recombination",
    assembly_method=GibsonAssemblyMethod(
        overhang_selector=FixedSizeSegmentSelector(300),
        min_segment_length=15000,
        max_segment_length=25000,
        duration=8
    ),
    supplier=blocks_assembly_comparator,
    coarse_grain=2000,
    fine_grain=200,
    logger='bar'
)

sequence_path = os.path.join("50kb_sequence.txt")
with open(sequence_path, "r") as f:
    sequence = f.read()

chunks_assembly_station.prepare_network_on_sequence(sequence)
quote = chunks_assembly_station.get_quote(sequence, with_assembly_plan=True)

print (quote.assembly_step_summary())
print ("Generating report...")
write_full_report(quote, "report.zip")
print ("Done! (see report.zip)")