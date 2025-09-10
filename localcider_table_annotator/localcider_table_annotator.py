from localcider.sequenceParameters import SequenceParameters
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import sys


def get_localcider_features(
    sequence_str, quantities: list | None = None
):
    """Get localCIDER features for a given sequence string.

    Parameters
    ----------
    sequence_str : str
        Amino acid sequence.
    quantities : list, optional
        List of localCIDER quantities to compute. If None, compute all.
    Returns
    -------
    dict
        Dictionary containing the localCIDER features.
    """
    Seqob = SequenceParameters(sequence_str)
    d = {
        "isoelectric_point": Seqob.get_isoelectric_point(),
        "n pos residues": Seqob.get_countPos(),
        "n neg residues": Seqob.get_countNeg(),
        "n neutral residues": Seqob.get_countNeut(),
        "net charge per residue": Seqob.get_NCPR(),
        "charge (n pos - n neg)": Seqob.get_countPos() - Seqob.get_countNeg(),
        "mean_net_charge": Seqob.get_mean_net_charge(),
        "fraction_positive": Seqob.get_fraction_positive(),
        "fraction_negative": Seqob.get_fraction_negative(),
        "fraction_expanding": Seqob.get_fraction_expanding(),
        "uversky_hydropathy": Seqob.get_uversky_hydropathy(),
        "mean_hydropathy": Seqob.get_mean_hydropathy(),
        "PPII_propensity": Seqob.get_PPII_propensity(),
        "Omega": Seqob.get_Omega(),
        "kappa": Seqob.get_kappa(),
        "sequence": sequence_str,
    }
    if quantities is not None:
        d = {k: v for k, v in d.items() if k in quantities or k == "sequence"}
    return d


def add_localcider_features_to_dataframe(
    dfin, sequence_colname: str = "sequence", quantities: list | None = None, ask_overwrite: bool = False
):
    df = dfin.copy()
    if sequence_colname not in df.columns:
        raise ValueError(f"DataFrame must contain '{sequence_colname}' column")
    localcider_dicts = []
    for seq in df[sequence_colname]:
        if not isinstance(seq, str) or len(seq) == 0:
            print(f"Warning: Skipping invalid sequence: {seq}")
            # localcider_dicts.append({sequence_colname: seq})
            continue
        d = get_localcider_features(
            seq, quantities=quantities
        )
        localcider_dicts.append(d)
    localcider_df = pd.DataFrame(localcider_dicts)
    # Check for overlapping column names
    overlapping_cols = set(df.columns) & set(localcider_df.columns)
    overlapping_cols.discard(sequence_colname)
    if overlapping_cols:
        if not ask_overwrite:
            print(f"Columns {overlapping_cols} already exist in DataFrame. They will be overwritten.")
        else:
            response = input(
                f"Columns {overlapping_cols} already exist in DataFrame. Overwrite? (y/n): "
            )
            if response.lower() != "y":
                print("Operation cancelled.")
                return df
        df = df.drop(columns=overlapping_cols)
    localcider_df = localcider_df.drop_duplicates(subset=["sequence"])
    dfnew = pd.merge(
        df, localcider_df, left_on=sequence_colname, right_on="sequence", how="left",
    )
    if sequence_colname!="sequence":
        s1 = set([i for i in df[sequence_colname] if isinstance(i, str) and len(i)>0])
        s2 = set([i for i in localcider_df["sequence"] if isinstance(i, str) and len(i)>0])
        assert s1 == s2, f"sequences in original DataFrame ({len(s1)}) do not match processed sequences ({len(s2)})"
        # assert (dfnew[sequence_colname]==dfnew["sequence"]).all(), "Sequence columns do not match after merge"
        dfnew = dfnew.drop(columns=["sequence"])
    return dfnew


def main():
    parser = argparse.ArgumentParser(
        description="Add localCIDER features to a CSV file containing sequences.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "input_csv", type=str, help="Path to the input CSV file with sequences."
    )
    parser.add_argument(
        "--output_csv", type=str, default=None, help="if not given, it will add '_with_localcider' to the input filename"
    )
    parser.add_argument(
        "--sequence_colname",
        type=str,
        default="sequence",
        help="Column name containing sequences. Default is 'sequence'.",
    )
    parser.add_argument(
        "--quantities",
        type=str,
        nargs="+",
        default=None,
        help="List of localCIDER quantities to compute. Default is all.",
    )
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    if args.output_csv is None:
        output_path = input_path.with_name(input_path.stem + "_with_localcider.csv")
    else:
        output_path = Path(args.output_csv)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file {input_path} does not exist.")

    df = pd.read_csv(input_path)
    dfnew = add_localcider_features_to_dataframe(
        df, sequence_colname=args.sequence_colname, quantities=args.quantities, ask_overwrite=True
    )
    dfnew.to_csv(output_path, index=False)
    print(f"Output saved to {output_path}")
