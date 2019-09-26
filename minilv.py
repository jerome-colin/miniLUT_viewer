#!/usr/bin/env python3
"""
Simple minilut plotting utility (SENTINEL2 only)

usage: minilv.py [-h] [-v] [-b n] [-z z] FILE

positional arguments:
  FILE                  Maquette miniLut output

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Set verbosity to INFO level + interactive plotting
  -b, --band            Integer band index (B1 is 0)
  -z, --level           Integer altitude level (0m is 0)
Example:

    ./minilv.py -v -b 1 -z 0 21LWK_20170917_S2A_L1Csimu_toa_240m.minilut

"""

__author__ = "J.Colin, CESBIO"
__license__ = "CC BY"
__version__ = "0.1.0"

import os
import sys
import argparse
import numpy as np
import pylab as pl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE", help="MiniLut File")
    parser.add_argument("-v", "--verbose", \
                        help="Set verbosity to INFO level + interactive plotting", \
                        action="store_true")
    parser.add_argument("-b", "--band", type=int, \
                        help="Integer band number, defaults to 0", \
                        default=0)
    parser.add_argument("-z", "--level", type=int, \
                        help="Integer altitude level, defaults to 0", \
                        default=0)
    parser.add_argument("-a", "--all", \
                        help="Show all AOT values of miniLUT", \
                        action="store_true")

    args = parser.parse_args()

    # Setting miniLut dimensions (S2 only)
    nband  = np.arange(13)
    vband  = [444 ,496, 560, 664, 704, 740, 782, 832, 865, 944, 1373, 1613, 2198]
    rtoa   = np.arange(-0.2,1.2,0.07)
    tau    = np.linspace(0.,1.5,25)
    tau    = np.append(tau, [2.0, 3.0]) # For LUT up to 3.0 compat
    ftau   = "LUT30"                    # Flag for LUT up to 3.0
    alt    = np.arange(0,3100,1000)

    # Checking arguments
    if args.band > len(nband):
        print("ERROR: Band number out of range")
        sys.exit(1)

    if args.level > len(alt):
        print("ERROR: Level out of range")
        sys.exit(1)

    if args.verbose:
        print("INFO: working with band B%i" % (args.band+1))

    # Opening miniLut file
    try:
        with open(args.FILE, 'rb') as f:
            fdata = np.fromfile(f, dtype = np.float32)
            minilut = fdata.reshape(len(nband), \
                                    len(rtoa), \
                                    len(tau), \
                                    len(alt))
            
        if args.verbose:
            print("INFO: successfuly opened %s" % args.FILE)

    except ValueError:
        # Added for compat with former LUTs up to AOT 1.5
        print("WARNING: bad minilut dimensions, trying with AOT->1.5")
        tau    = np.linspace(0.,1.5,25)
        minilut = fdata.reshape(len(nband), \
                                    len(rtoa), \
                                    len(tau), \
                                    len(alt))
        ftau = "LUT15"

    except FileNotFoundError:
        print("ERROR: file %s not found..." % args.FILE)
        sys.exit(1)

    except:
        print("ERROR: Unexpected error:", sys.exc_info()[0])
        raise
        sys.exit(1)

    # Plotting rse = f(rtoa) for values au tau for band n
    fname = args.FILE[:-4]+"_B"+str(args.band+1)+"_L"+str(args.level)+".png"
    miniplot(rtoa, tau, minilut, alt, vband, fname, \
             args.band, args.level, ftau, args.verbose, args.all)

    print("INFO: Done...")
    sys.exit(0)


def miniplot(rtoa, tau, minilut, alt, vband, filename, \
             band = 0, level = 0, dims = "LUT30", verbose=False, showall=False):

    fig, ax1 = pl.subplots(1, 1, figsize=(6, 6))
    ax1.set_aspect('equal', 'box')
    pl.title("rse = f(rtoa), band %i nm, level = %6.1f m" % (vband[band], alt[level]))
    ax1.set_xlabel('rtoa')
    ax1.set_ylabel('rse')
    ax1.set_xlim(min(rtoa), max(rtoa))
    ax1.set_ylim(min(rtoa), max(rtoa))
    ax1.plot([min(rtoa), max(rtoa)], [min(rtoa), max(rtoa)], 'k--')

    # Arbitrary AOT sampling
    if dims == "LUT30":
        tau_sampling = [0, 8, 16, 24, 25, 26]
    elif dims == "LUT15":
        tau_sampling = [0, 8, 16, 24]

    # --all overloads previous sampling
    if showall:
        tau_sampling = range(len(tau))

    # Loop on AOT, plot and check monotony of rse=f(rtoa)
    for t in tau_sampling:
        ax1.plot(rtoa, minilut[band,:,t,level], label = "AOT=%4.2f" % tau[t])
        # Testing monotony for each AOT step:
        monotony = np.all(np.diff(minilut[band,:,t,level])>0)
        if not monotony:
            print("WARNING: non-monotone fitting for AOT=%4.2f" % tau[t])

    ax1.legend()

    try:
        pl.savefig(filename, format='png')

    except PermissionError:
        print("WARNING: write permission missing, couldn't save figure")

    if verbose:
        pl.show()

if __name__ == "__main__":
    main()
