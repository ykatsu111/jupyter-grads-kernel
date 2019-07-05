# GrADS kernel for Jupyter

This software a simple wrapper of GrADS.
You can execute any GrADS commands of native GrADS on you computer.


# Installation

Make sure you have the following requirements installed:

  * jupyter
  * python 3
  * pip
  * grads

Steps to install:

1. `git clone https://github.com/ykatsu111/jupyter-grads-kernel`
2. `pip install --user git+https://github.com/ykatsu111/jupyter-grads-kernel`
3. `cd jupyter-grads-kernel`
4. `jupyter kernelspec install --user grads_spec`

Then, a kernel "GrADS" will be seen in your jupyter notebook or lab.

# Uninstall

1. `jupyter kernelspec uninstall grads_spec`
2. `pip uninstall jupyter-grads-kernel`