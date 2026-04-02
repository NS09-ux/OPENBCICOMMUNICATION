from glob import glob

from setuptools import find_packages, setup

package_name = "gesture_interpreter_ros"

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
    description="ROS 2 EMG gesture interpreter node",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "gesture_interpreter_node = gesture_interpreter_ros.gesture_node:main",
        ],
    },
)
