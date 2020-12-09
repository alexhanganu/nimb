import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nimb",
    version="0.0.1",
    author="Alexandru Hanganu",
    author_email="alexandru.hanganu@umontreal.ca",
    description="NIMB = NeuroImaging My Brain: app to classify MRI data, distribute to local or remote servers, initiate processing with FreeSurfer, nilearn, dipy, extract stats, perform general statistics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alexhanganu/nimb",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
