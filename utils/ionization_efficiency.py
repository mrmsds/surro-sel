"""Utility class to calculate ionization efficiency embedding.

This class uses the Mordred descriptor calculator to compute ionization
efficiency descriptors from SMILES using RDKit and applies TSNE for
dimensionality reduction.

The use of this embedding was proposed by Charest et al. (2025):
DOI:10.1007/s00216-025-05919-8.
"""

import numpy as np
import pandas as pd
from mordred import Calculator, MoeType, EState, MolecularId
from rdkit.Chem import MolFromSmiles
from rdkit import RDLogger
from sklearn.manifold import TSNE
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


class IonizationEfficiency:
    """Utility class for ionization efficiency descriptors and TSNE."""

    # Embedding column names
    EMBEDDING = (
        ['AMID_N', 'AMID_C', 'AMID_O', 'SsssN', 'SdO']
        + [f'EState_VSA{i}' for i in range(1, 11)]
        + [f'PEOE_VSA{i}' for i in range(1, 14)]
    )

    # Mordred calculator object with custom embedding
    _desc_calculator = Calculator([
        # AMID_N, AMID_C, AMID_O
        MolecularId.MolecularId(averaged=True, type='N'),
        MolecularId.MolecularId(averaged=True, type='C'),
        MolecularId.MolecularId(averaged=True, type='O'),
        # SsssN, SdO
        EState.AtomTypeEState(type=str(EState.AggrType.sum), estate='sssN'),
        EState.AtomTypeEState(type=str(EState.AggrType.sum), estate='dO'),
        # EState_VSA{1:10}
        MoeType.EState_VSA,
        # PEOE_VSA{1:13}
        MoeType.PEOE_VSA
    ])

    # TSNE calculation pipeline with feature standardization
    _tsne_pipeline = make_pipeline(StandardScaler(), TSNE(random_state=2025))

    @staticmethod
    def calculate(smiles, index, with_tsne):
        """Calculate descriptors and optional TSNE embedding for structures.
        
        Args:
            smiles: standardized SMILES strings to calculate descriptors for
            index: index values to attach to the resulting df
            with_tsne: include TSNE coordinates in output?
        Returns:
            df of descriptors and (optional) TSNE coordinates
        """

        # Hack around RDKit native stderr warnings
        RDLogger.DisableLog('rdApp.*')

        # Attempt molecule conversion from SMILES
        mols = np.array(
            [MolFromSmiles(str(smi), sanitize=False) for smi in smiles])
        # Locate conversion failures and replace with placeholders
        bad_idx = np.where(np.array(mols) == None)[0]
        mols[bad_idx] = MolFromSmiles('', sanitize=False)

        # Calculate ionization efficiency descriptors
        # nproc=1 avoids paging space issues in Shiny deployment
        desc = IonizationEfficiency._desc_calculator.pandas(
            mols, nproc=1, quiet=True)
        # Remove placeholder descriptors from invalid structures
        desc.drop(labels=bad_idx, inplace=True)
        # Attach index values
        desc.index = index

        # Optionally calculate and append TSNE coordinates
        if with_tsne:
            desc[['TSNE1', 'TSNE2']] = pd.DataFrame(
                IonizationEfficiency._tsne_pipeline.fit_transform(desc),
                index=desc.index
            )

        return desc
