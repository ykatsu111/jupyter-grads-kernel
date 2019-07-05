from setuptools import setup

setup(name='jupyter_grads_kernel',
      version='0.1.0',
      description='GrADS kernel for Jupyter',
      author='ykatsu111',
      url='https://github.com/ykatsu111/jupyter-grads-kernel',
      license='MIT',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Framework :: IPython',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Fortran',
      ],
      packages=['jupyter_fortran_kernel'],
      keywords=['jupyter', 'kernel', 'fortran']
)
