#  Copyright (c) 2022. RadonPy developers. All rights reserved.
#  Use of this source code is governed by a BSD-3-style
#  license that can be found in the LICENSE file.

# ******************************************************************************
# core.utils module
# ******************************************************************************

import os
import psutil
from copy import deepcopy
from itertools import permutations
import numpy as np
import pickle
from rdkit import Chem
from rdkit.Chem import AllChem
from . import const

__version__ = '0.2.3'


class Angle():
    """
        utils.Angle() object
    """
    def __init__(self, a, b, c, ff):
        self.a = a
        self.b = b
        self.c = c
        self.ff = ff
    
    
class Dihedral():
    """
        utils.Dihedral() object
    """
    def __init__(self, a, b, c, d, ff):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.ff = ff
    
    
class Improper():
    """
        utils.Improper() object
    """
    def __init__(self, a, b, c, d, ff):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.ff = ff


class Angle_ff():
    """
        utils.Angle_ff() object
    """
    def __init__(self, ff_type=None, k=None, theta0=None):
        self.type = ff_type
        self.k = k
        self.theta0 = theta0
        self.theta0_rad = theta0*(np.pi/180)
    
    
class Dihedral_ff():
    """
        utils.Dihedral_ff() object
    """
    def __init__(self, ff_type=None, k=[], d0=[], m=None, n=[]):
        self.type = ff_type
        self.k = np.array(k)
        self.d0 = np.array(d0)
        self.d0_rad = np.array(d0)*(np.pi/180)
        self.m = m
        self.n = np.array(n)
    
    
class Improper_ff():
    """
        utils.Improper_ff() object
    """
    def __init__(self, ff_type=None, k=None, d0=-1, n=None):
        self.type = ff_type
        self.k = k
        self.d0 = d0
        self.n = n
    
        
class Cell():
    def __init__(self, xhi, xlo, yhi, ylo, zhi, zlo):
        self.xhi = xhi
        self.xlo = xlo
        self.yhi = yhi
        self.ylo = ylo
        self.zhi = zhi
        self.zlo = zlo
        self.dx = xhi-xlo
        self.dy = yhi-ylo
        self.dz = zhi-zlo
        self.volume = self.dx * self.dy * self.dz


class RadonPyError(Exception):
    pass


def radon_print(text, level=0):
    if level == 0:
        text = 'RadonPy debug info: '+text
    elif level == 1:
        text = 'RadonPy info: '+text
    elif level == 2:
        text = 'RadonPy warning: '+text
    elif level == 3:
        raise RadonPyError(text)

    if level >= const.print_level or const.debug:
        print(text, flush=True)


def set_mol_id(mol, pdb=True):
    """
    utils.set_mol_id

    Set molecular ID

    Args:
        mol: RDkit Mol object

    Optional args:
        pdb: Update the ChainId of PDB (boolean)

    Returns:
        Rdkit Mol object
    """

    molid = 1

    # Clear mol_id
    for atom in mol.GetAtoms():
        atom.SetIntProp('mol_id', 0)

    def recursive_set_mol_id(atom, molid):
        for na in atom.GetNeighbors():
            if na.GetIntProp('mol_id') == 0:
                na.SetIntProp('mol_id', molid)
                if pdb and na.GetPDBResidueInfo() is not None:
                    if molid <= len(const.pdb_id):
                        na.GetPDBResidueInfo().SetChainId(const.pdb_id[molid-1])
                recursive_set_mol_id(na, molid)

    for atom in mol.GetAtoms():
        if atom.GetIntProp('mol_id') == 0:
            atom.SetIntProp('mol_id', molid)
            if pdb and atom.GetPDBResidueInfo() is not None:
                if molid <= len(const.pdb_id):
                    atom.GetPDBResidueInfo().SetChainId(const.pdb_id[molid-1])
            recursive_set_mol_id(atom, molid)
            molid += 1

    return mol


def count_mols(mol):
    """
    utils.count_mols

    Count number of molecules

    Args:
        mol: RDkit Mol object

    Returns:
        Number of molecules (int)
    """

    molid = 1
    molcount = 0

    # Clear mol_id
    for atom in mol.GetAtoms():
        atom.SetIntProp('mol_id', 0)

    def recursive_count_mols(atom, molid):
        for na in atom.GetNeighbors():
            if na.GetIntProp('mol_id') == 0:
                na.SetIntProp('mol_id', molid)
                recursive_count_mols(na, molid)

    for atom in mol.GetAtoms():
        if atom.GetIntProp('mol_id') == 0:
            atom.SetIntProp('mol_id', molid)
            recursive_count_mols(atom, molid)
            molid += 1
            molcount += 1

    return molcount


def remove_atom(mol, idx):
    """
    utils.remove_atom

    Remove a specific atom from RDkit Mol object

    Args:
        mol: RDkit Mol object
        idx: Atom index of removing atom in RDkit Mol object

    Returns:
        RDkit Mol object
    """

    angles_copy = []
    dihedrals_copy = []
    impropers_copy = []
    cell_copy = None

    if hasattr(mol, 'cell'):
        cell_copy = mol.cell

    if hasattr(mol, 'impropers'):
        for imp in mol.impropers:
            if idx in [imp.a, imp.b, imp.c, imp.d]:
                continue
            idx_a = imp.a if imp.a < idx else imp.a-1
            idx_b = imp.b if imp.b < idx else imp.b-1
            idx_c = imp.c if imp.c < idx else imp.c-1
            idx_d = imp.d if imp.d < idx else imp.d-1
            impropers_copy.append(
                Improper(
                    a=idx_a,
                    b=idx_b,
                    c=idx_c,
                    d=idx_d,
                    ff=deepcopy(imp.ff)
                )
            )

    if hasattr(mol, 'dihedrals'):
        for dih in mol.dihedrals:
            if idx in [dih.a, dih.b, dih.c, dih.d]:
                continue
            idx_a = dih.a if dih.a < idx else dih.a-1
            idx_b = dih.b if dih.b < idx else dih.b-1
            idx_c = dih.c if dih.c < idx else dih.c-1
            idx_d = dih.d if dih.d < idx else dih.d-1
            dihedrals_copy.append(
                Dihedral(
                    a=idx_a,
                    b=idx_b,
                    c=idx_c,
                    d=idx_d,
                    ff=deepcopy(dih.ff)
                )
            )

    if hasattr(mol, 'angles'):
        for angle in mol.angles:
            if idx in [angle.a, angle.b, angle.c]:
                continue
            idx_a = angle.a if angle.a < idx else angle.a-1
            idx_b = angle.b if angle.b < idx else angle.b-1
            idx_c = angle.c if angle.c < idx else angle.c-1
            angles_copy.append(
                Angle(
                    a=idx_a,
                    b=idx_b,
                    c=idx_c,
                    ff=deepcopy(angle.ff)
                )
            )

    rwmol = Chem.RWMol(mol)
    for pb in mol.GetAtomWithIdx(idx).GetNeighbors():
        rwmol.RemoveBond(idx, pb.GetIdx())

    rwmol.RemoveAtom(idx)

    mol = rwmol.GetMol()
    setattr(mol, 'angles', angles_copy)
    setattr(mol, 'dihedrals', dihedrals_copy)
    setattr(mol, 'impropers', impropers_copy)
    if cell_copy is not None: setattr(mol, 'cell', cell_copy)

    return mol


def add_bond(mol, idx1, idx2, order=Chem.rdchem.BondType.SINGLE):
    """
    utils.add_bond

    Add a new bond in RDkit Mol object

    Args:
        mol: RDkit Mol object
        idx1, idx2: Atom index adding a new bond (int)
        order: bond order (RDkit BondType object, ex. Chem.rdchem.BondType.SINGLE)

    Returns:
        RDkit Mol object
    """

    # Copy the extended attributes
    angles_copy = mol.angles if hasattr(mol, 'angles') else []
    dihedrals_copy = mol.dihedrals if hasattr(mol, 'dihedrals') else []
    impropers_copy = mol.impropers if hasattr(mol, 'impropers') else []
    cell_copy = mol.cell if hasattr(mol, 'cell') else None

    rwmol = Chem.RWMol(mol)
    rwmol.AddBond(idx1, idx2, order=order)
    mol = rwmol.GetMol()

    setattr(mol, 'angles', angles_copy)
    setattr(mol, 'dihedrals', dihedrals_copy)
    setattr(mol, 'impropers', impropers_copy)
    if cell_copy is not None: setattr(mol, 'cell', cell_copy)

    return mol


def remove_bond(mol, idx1, idx2):
    """
    utils.remove_bond

    Remove a specific bond in RDkit Mol object

    Args:
        mol: RDkit Mol object
        idx1, idx2: Atom index removing a specific bond (int)

    Returns:
        RDkit Mol object
    """

    # Copy the extended attributes
    angles_copy = mol.angles if hasattr(mol, 'angles') else []
    dihedrals_copy = mol.dihedrals if hasattr(mol, 'dihedrals') else []
    impropers_copy = mol.impropers if hasattr(mol, 'impropers') else []
    cell_copy = mol.cell if hasattr(mol, 'cell') else None

    rwmol = Chem.RWMol(mol)
    rwmol.RemoveBond(idx1, idx2)
    mol = rwmol.GetMol()

    setattr(mol, 'angles', angles_copy)
    setattr(mol, 'dihedrals', dihedrals_copy)
    setattr(mol, 'impropers', impropers_copy)
    if cell_copy is not None: setattr(mol, 'cell', cell_copy)

    return mol


def add_angle(mol, a, b, c, ff=None):
    """
    utils.add_angle

    Add a new angle in RDkit Mol object

    Args:
        mol: RDkit Mol object
        a, b, c: Atom index adding a new angle (int)

    Returns:
        boolean
    """

    if not hasattr(mol, 'angles'):
        setattr(mol, 'angles', [])

    mol.angles.append(
        Angle(
            a=a,
            b=b,
            c=c,
            ff=ff
        )
    )

    return True


def remove_angle(mol, a, b, c):
    """
    utils.remove_angle

    Remove a specific angle in RDkit Mol object

    Args:
        mol: RDkit Mol object
        a, b, c: Atom index removing a specific angle (int)

    Returns:
        boolean
    """

    if not hasattr(mol, 'angles'):
        return False

    for i, angle in enumerate(mol.angles):
        if ((angle.a == a and angle.b == b and angle.c == c) or
            (angle.c == a and angle.b == b and angle.a == c)):
            del mol.angles[i]
            break

    return True


def add_dihedral(mol, a, b, c, d, ff=None):
    """
    utils.add_dihedral

    Add a new dihedral in RDkit Mol object

    Args:
        mol: RDkit Mol object
        a, b, c, d: Atom index adding a new dihedral (int)

    Returns:
        boolean
    """

    if not hasattr(mol, 'dihedrals'):
        setattr(mol, 'dihedrals', [])

    mol.dihedrals.append(
        Dihedral(
            a=a,
            b=b,
            c=c,
            d=d,
            ff=ff
        )
    )

    return True
    

def remove_dihedral(mol, a, b, c, d):
    """
    utils.remove_dihedral

    Remove a specific dihedral in RDkit Mol object

    Args:
        mol: RDkit Mol object
        a, b, c: Atom index removing a specific dihedral (int)

    Returns:
        boolean
    """

    if not hasattr(mol, 'dihedrals'):
        return False

    for i, dihedral in enumerate(mol.dihedrals):
        if ((dihedral.a == a and dihedral.b == b and dihedral.c == c and dihedral.d == d) or
            (dihedral.d == a and dihedral.c == b and dihedral.b == c and dihedral.a == d)):
            del mol.dihedrals[i]
            break

    return True


def add_improper(mol, a, b, c, d, ff=None):
    """
    utils.add_improper

    Add a new imploper in RDkit Mol object

    Args:
        mol: RDkit Mol object
        a, b, c, d: Atom index adding a new imploper (int)

    Returns:
        boolean
    """

    if not hasattr(mol, 'impropers'):
        setattr(mol, 'impropers', [])

    mol.impropers.append(
        Improper(
            a=a,
            b=b,
            c=c,
            d=d,
            ff=ff
        )
    )

    return True
    

def remove_improper(mol, a, b, c, d):
    """
    utils.remove_improper

    Remove a specific improper in RDkit Mol object

    Args:
        mol: RDkit Mol object
        a, b, c: Atom index removing a specific improper (int)

    Returns:
        boolean
    """

    if not hasattr(mol, 'impropers'):
        return False

    match = False
    for i, improper in enumerate(mol.impropers):
        if improper.a == a:
            for perm in permutations([b, c, d], 3):
                if improper.b == perm[0] and improper.c == perm[1] and improper.d == perm[2]:
                    del mol.impropers[i]
                    match = True
                    break
            if match: break

    return True


def MolToPDBBlock(mol, confId=0):
    """
    utils.MolToPDBBlock

    Convert RDKit Mol object to PDB block

    Args:
        mol: RDkit Mol object

    Optional args:
        confId: Target conformer ID (int)

    Returns:
        PDB block (str, array)
    """

    coord = mol.GetConformer(confId).GetPositions()
    PDBBlock = ['TITLE    pdb written using RadonPy']
    conect = []
    serial = 0
    ter = 0
    chainid_pre = 1
    chainid_pdb_pre = ''

    for i, atom in enumerate(mol.GetAtoms()):
        serial += 1
        resinfo = atom.GetPDBResidueInfo()
        if resinfo is None: return None

        chainid_pdb = resinfo.GetChainId()
        chainid = atom.GetIntProp('mol_id')
        if chainid != chainid_pre:
            if chainid_pdb_pre:
                PDBBlock.append('TER   %5i      %3s %1s%4i%1s' % (serial, resname, chainid_pdb_pre, resnum, icode))
            else:
                PDBBlock.append('TER   %5i      %3s %1s%4i%1s' % (serial, resname, '*', resnum, icode))
            ter += 1
            serial += 1

        record = 'HETATM' if resinfo.GetIsHeteroAtom() else 'ATOM  '
        name = atom.GetProp('ff_type') if atom.HasProp('ff_type') else atom.GetSymbol()
        altLoc = resinfo.GetAltLoc()
        resname = resinfo.GetResidueName()
        resnum = resinfo.GetResidueNumber()
        icode = resinfo.GetInsertionCode()
        x = coord[i][0]
        y = coord[i][1]
        z = coord[i][2]
        occ = resinfo.GetOccupancy() if resinfo.GetOccupancy() else 1.0
        tempf = resinfo.GetTempFactor() if resinfo.GetTempFactor() else 0.0

        if chainid_pdb:
            line = '%-6s%5i %4s%1s%3s %1s%4i%1s   %8.3f%8.3f%8.3f%6.2f%6.2f          %2s' % (
                    record, serial, name, altLoc, resname, chainid_pdb, resnum, icode, x, y, z, occ, tempf, atom.GetSymbol())
        else:
            line = '%-6s%5i %4s%1s%3s %1s%4i%1s   %8.3f%8.3f%8.3f%6.2f%6.2f          %2s' % (
                    record, serial, name, altLoc, resname, '*', resnum, icode, x, y, z, occ, tempf, atom.GetSymbol())

        PDBBlock.append(line)

        chainid_pre = chainid
        chainid_pdb_pre = chainid_pdb

        if len(atom.GetNeighbors()) > 0:
            flag = False
            conect_line = 'CONECT%5i' % (serial)
            for na in atom.GetNeighbors():
                if atom.GetIdx() < na.GetIdx():
                    conect_line += '%5i' % (na.GetIdx()+1+ter)
                    flag = True
            if flag:
                conect.append(conect_line)

    PDBBlock.append('TER   %5i      %3s %1s%4i%1s' % (serial+1, resname, chainid_pre, resnum, icode))
    PDBBlock.extend(conect)
    PDBBlock.append('END')

    return PDBBlock


def MolToPDBFile(mol, filename, confId=0):
    """
    utils.MolToPDBFile

    Convert RDKit Mol object to PDB file

    Args:
        mol: RDkit Mol object
        filename: Output pdb filename (str)

    Optional args:
        confId: Target conformer ID (int)

    Returns:
        Success or fail (boolean)
    """

    mol = set_mol_id(mol)
    PDBBlock = MolToPDBBlock(mol, confId=confId)
    if PDBBlock is None: return False

    with open(filename, 'w') as fh:
        fh.write('\n'.join(PDBBlock)+'\n')
        fh.flush()
        if hasattr(os, 'fdatasync'):
            os.fdatasync(fh.fileno())
        else:
            os.fsync(fh.fileno())

    return True


def StructureFromXYZFile(filename):
    with open(filename, 'r') as fh:
        lines = [s.strip() for s in fh.readlines()]

    strucs = []
    struc = []
    t_flag = False
    n_flag = False
    n_atom = 0
    c_atom = 0
    for line in lines:
        if not n_flag:
            if line.isdecimal():
                n_atom = line
                n_flag = True
        elif not t_flag:
            t_flag = True
            continue
        else:
            c_atom += 1
            element, x, y, z = line.split()
            struc.append([element, x, y, z])
            if c_atom >= n_atom:
                strucs.append(struc)
                t_flag = False
                n_flag = False
                n_atom = 0
                c_atom = 0

    return strucs


def MolToExXYZBlock(mol, confId=0):

    XYZBlock = Chem.MolToXYZBlock(mol, confId=confId)
    XYZBlock = XYZBlock.split('\n')
    if mol.GetConformer(confId).HasProp('cell_xhi'):
        conf = mol.GetConformer(confId)
        cell_line = 'Lattice=\"%.4f 0.0 0.0 0.0 %.4f 0.0 0.0 0.0 %.4f\"' % (
            conf.GetDoubleProp('cell_dx'), conf.GetDoubleProp('cell_dy'), conf.GetDoubleProp('cell_dz'))
        XYZBlock[1] = cell_line
    elif hasattr(mol, 'cell'):
        cell_line = 'Lattice=\"%.4f 0.0 0.0 0.0 %.4f 0.0 0.0 0.0 %.4f\"' % (mol.cell.dx, mol.cell.dy, mol.cell.dz)
        XYZBlock[1] = cell_line

    return XYZBlock


def MolToExXYZFile(mol, filename, confId=0):

    XYZBlock = MolToExXYZBlock(mol, confId=confId)
    if XYZBlock is None: return False
    with open(filename, 'w') as fh:
        fh.write('\n'.join(XYZBlock)+'\n')
        fh.flush()
        if hasattr(os, 'fdatasync'):
            os.fdatasync(fh.fileno())
        else:
            os.fsync(fh.fileno())

    return True


def picklable(mol):
    Chem.SetDefaultPickleProperties(Chem.PropertyPickleOptions.AllProps)
    return mol


def picklable_old(mol):
    
    Chem.SetDefaultPickleProperties(Chem.PropertyPickleOptions.AllProps)
    if hasattr(mol, 'angles'):
        for angle in mol.angles:
            if type(angle.a) is Chem.Atom:
                angle.a = angle.a.GetIdx()
            if type(angle.b) is Chem.Atom:
                angle.b = angle.b.GetIdx()
            if type(angle.c) is Chem.Atom:
                angle.c = angle.c.GetIdx()
        
    if hasattr(mol, 'dihedrals'):
        for dih in mol.dihedrals:
            if type(dih.a) is Chem.Atom:
                dih.a = dih.a.GetIdx()
            if type(dih.b) is Chem.Atom:
                dih.b = dih.b.GetIdx()
            if type(dih.c) is Chem.Atom:
                dih.c = dih.c.GetIdx()
            if type(dih.d) is Chem.Atom:
                dih.d = dih.d.GetIdx()
        
    if hasattr(mol, 'impropers'):
        for imp in mol.impropers:
            if type(imp.a) is Chem.Atom:
                imp.a = imp.a.GetIdx()
            if type(imp.b) is Chem.Atom:
                imp.b = imp.b.GetIdx()
            if type(imp.c) is Chem.Atom:
                imp.c = imp.c.GetIdx()
            if type(imp.d) is Chem.Atom:
                imp.d = imp.d.GetIdx()

    return mol


def restore_picklable(mol):
    return mol


def restore_picklable_old(mol):

    if hasattr(mol, 'angles'):
        for angle in mol.angles:
            if type(angle.a) is int:
                angle.a = mol.GetAtomWithIdx(angle.a)
            if type(angle.b) is int:
                angle.b = mol.GetAtomWithIdx(angle.b)
            if type(angle.c) is int:
                angle.c = mol.GetAtomWithIdx(angle.c)
        
    if hasattr(mol, 'dihedrals'):
        for dih in mol.dihedrals:
            if type(dih.a) is int:
                dih.a = mol.GetAtomWithIdx(dih.a)
            if type(dih.b) is int:
                dih.b = mol.GetAtomWithIdx(dih.b)
            if type(dih.c) is int:
                dih.c = mol.GetAtomWithIdx(dih.c)
            if type(dih.d) is int:
                dih.d = mol.GetAtomWithIdx(dih.d)
        
    if hasattr(mol, 'impropers'):
        for imp in mol.impropers:
            if type(imp.a) is int:
                imp.a = mol.GetAtomWithIdx(imp.a)
            if type(imp.b) is int:
                imp.b = mol.GetAtomWithIdx(imp.b)
            if type(imp.c) is int:
                imp.c = mol.GetAtomWithIdx(imp.c)
            if type(imp.d) is int:
                imp.d = mol.GetAtomWithIdx(imp.d)

    return mol


def pickle_dump(mol, path):
    Chem.SanitizeMol(mol)
    mol = picklable(mol)
    with open(path, mode='wb') as f:
        pickle.dump(mol, f)


def pickle_load(path):
    try:
        with open(path, mode='rb') as f:
            mol = pickle.load(f)
    except:
        return None
    return mol


def deepcopy_mol(mol):
    mol = picklable(mol)
    copy_mol = deepcopy(mol)

    return copy_mol


def cpu_count():
    try:
        cpu_count = len(os.sched_getaffinity(0))
    except AttributeError as e:
        cpu_count = psutil.cpu_count(logical=False)
        if cpu_count is None:
            cpu_count = psutil.cpu_count(logical=True)

    return cpu_count


def tqdm_stub(it, **kwargs):
    return it


def mol_from_smiles(smiles, coord=True, version=2, ez='E', chiral='S'):

    n_conn = smiles.count('[*]') + smiles.count('*') + smiles.count('[3H]')
    smi = smiles.replace('[*]', '[3H]')
    smi = smi.replace('*', '[3H]')

    if version == 3:
        etkdg = AllChem.ETKDGv3()
    elif version == 2:
        etkdg = AllChem.ETKDGv2()
    else:
        etkdg = AllChem.ETKDG()
    etkdg.enforceChirality=True
    etkdg.useRandomCoords = False
    etkdg.maxAttempts = 100

    try:
        mol = Chem.MolFromSmiles(smi)
        mol = Chem.AddHs(mol)
    except Exception as e:
        radon_print('Cannot transform to RDKit Mol object from %s' % smiles, level=3)
        return None

    ### cis/trans and chirality control
    Chem.AssignStereochemistry(mol)

    # Get polymer backbone
    backbone_atoms = []
    backbone_bonds = []
    backbone_dih = []

    if n_conn == 2:
        link_idx = []
        for atom in mol.GetAtoms():
            if atom.GetSymbol() == "H" and atom.GetIsotope() == 3:
                link_idx.append(atom.GetIdx())
        backbone_atoms = Chem.GetShortestPath(mol, link_idx[0], link_idx[1])

        for i in range(len(backbone_atoms)-1):
            bond = mol.GetBondBetweenAtoms(backbone_atoms[i], backbone_atoms[i+1])
            backbone_bonds.append(bond.GetIdx())
            if bond.GetBondTypeAsDouble() == 2 and str(bond.GetStereo()) == 'STEREONONE' and not bond.IsInRing():
                backbone_dih.append((backbone_atoms[i-1], backbone_atoms[i], backbone_atoms[i+1], backbone_atoms[i+2]))

    # List of unspecified double bonds (except for bonds in polymer backbone and a ring structure)
    db_list = []
    for bond in mol.GetBonds():
        if bond.GetBondTypeAsDouble() == 2 and str(bond.GetStereo()) == 'STEREONONE' and not bond.IsInRing():
            if n_conn == 2 and bond.GetIdx() in backbone_bonds:
                continue
            else:
                db_list.append(bond.GetIdx())

    # Enumerate stereo isomers
    opts = Chem.EnumerateStereoisomers.StereoEnumerationOptions(unique=True, tryEmbedding=True)
    isomers = tuple(Chem.EnumerateStereoisomers.EnumerateStereoisomers(mol, options=opts))

    if len(isomers) > 1:
        radon_print('%i candidates of stereoisomers were generated.' % len(isomers))
        chiral_num_max = 0
        
        for isomer in isomers:
            ez_flag = False
            chiral_flag = 0

            Chem.AssignStereochemistry(isomer)

            # Contorol unspecified double bonds (except for bonds in polymer backbone and a ring structure)
            ez_list = []
            for idx in db_list:
                bond = isomer.GetBondWithIdx(idx)
                if str(bond.GetStereo()) == 'STEREOANY' or str(bond.GetStereo()) == 'STEREONONE':
                    continue
                elif ez == 'E' and (str(bond.GetStereo()) == 'STEREOE' or str(bond.GetStereo()) == 'STEREOTRANS'):
                    ez_list.append(True)
                elif ez == 'Z' and (str(bond.GetStereo()) == 'STEREOZ' or str(bond.GetStereo()) == 'STEREOCIS'):
                    ez_list.append(True)
                else:
                    ez_list.append(False)

            if len(ez_list) > 0:
                ez_flag = np.all(np.array(ez_list))
            else:
                ez_flag = True

            # Contorol unspecified chirality
            chiral_list = np.array(Chem.FindMolChiralCenters(isomer))
            if len(chiral_list) > 0:
                chiral_centers = chiral_list[:, 0]

                chirality = chiral_list[:, 1]
                chiral_num = np.count_nonzero(chirality == chiral)
                if chiral_num == len(chiral_list):
                    chiral_num_max = chiral_num
                    chiral_flag = 2
                elif chiral_num > chiral_num_max:
                    chiral_num_max = chiral_num
                    chiral_flag = 1
            else:
                chiral_flag = 2

            if ez_flag and chiral_flag:
                mol = isomer
                if chiral_flag == 2:
                    break

    # Generate 3D coordinates
    if coord:
        try:
            enbed_res = AllChem.EmbedMolecule(mol, etkdg)
        except Exception as e:
            radon_print('Cannot generate 3D coordinate of %s' % smiles, level=3)
            return None
        if enbed_res == -1:
            etkdg.useRandomCoords = True
            enbed_res = AllChem.EmbedMolecule(mol, etkdg)
            if enbed_res == -1:
                radon_print('Cannot generate 3D coordinate of %s' % smiles, level=3)
                return None

    # Dihedral angles of unspecified double bonds in a polymer backbone are modified to 180 degree.
    if len(backbone_dih) > 0:
        for dih_idx in backbone_dih:
            Chem.rdMolTransforms.SetDihedralDeg(mol.GetConformer(0), dih_idx[0], dih_idx[1], dih_idx[2], dih_idx[3], 180.0)

            for na in mol.GetAtomWithIdx(dih_idx[2]).GetNeighbors():
                na_idx = na.GetIdx()
                if na_idx != dih_idx[1] and na_idx != dih_idx[3]:
                    break
            Chem.rdMolTransforms.SetDihedralDeg(mol.GetConformer(0), dih_idx[0], dih_idx[1], dih_idx[2], na_idx, 0.0)

    return mol


def is_in_ring(ab, max_size=10):

    for i in range(3, max_size+1):
        if ab.IsInRingSize(int(i)):
            return True
    return False


def picklable_const():
    c = {}
    for v in dir(const):
        if v.count('__') != 2 and v != 'os':
            c[v] = getattr(const, v)
    return c


def restore_const(c):
    for k, v in c.items():
        setattr(const, k, v)
    return True
