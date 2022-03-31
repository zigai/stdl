from setuptools import find_packages, setup
import pathlib

with open('./requirements.txt') as f:
    requirements = f.read().splitlines()
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(name="stdl",
      version="0.0.1",
      description="Extended Python Standard Library",
      long_description=README,
      author="Ziga Ivansek",
      author_email="ziga.ivansek@gmail.com",
      url="https://github.com/ziga-ivansek/stdl",
      license="MIT",
      classifiers=[
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: 3.9",
          "Programming Language :: Python :: 3.10",
          "Programming Language :: Python :: 3 :: Only",
          "Topic :: Software Development :: Libraries :: Python Modules",
      ],
      packages=find_packages(),
      install_requires=requirements)
