import setuptools

setuptools.setup(
    name="statement_parser",
    version="0.1.0",
    author="timothy",
    author_email="timmy.ong.90@gmail.com",
    description="Library to parse statements from various financial instiutions",
    url="https://github.com/ttimong/statement_parser.git",
    include_package_data=True,
    install_requires=[
        "pdfplumber==0.11.4",
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    extras_require={
        "dev": ["pre-commit==3.7.0", "pylint==3.1.0"],
    },
)
