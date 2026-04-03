from glob import glob

from setuptools import find_packages, setup

package_name = "cyton_emg_ros"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Hadimani Lab",
    maintainer_email="lab@example.com",
    description="Cyton BrainFlow bridge to /emg_commands",
    license="MIT",
    entry_points={
        "console_scripts": [
            "cyton_emg_publisher = cyton_emg_ros.cyton_emg_publisher:main",
        ],
    },
)
