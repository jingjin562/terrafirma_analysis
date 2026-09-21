#!/bin/bash
#SBATCH --account=ocean_ice
#SBATCH --partition=standard
#SBATCH --qos=high
#SBATCH -n 4
#SBATCH -o %j.oe
#SBATCH -e %j.oe
#SBATCH --time=24:00:00
#SBATCH --mem=128G


module load jaspy

# python /home/users/jingj/terrafirma_analysis/utils/grid_extraction.py 
python run_dn026_global.py 
