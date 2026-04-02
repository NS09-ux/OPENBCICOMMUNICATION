from setuptools import setup

package_name = "gesture_interpreter"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name, f"{package_name}.sim"],
    package_dir={package_name: "."},
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Hadimani Lab",
    maintainer_email="lab@example.com",
    description="EMG gesture interpreter core library",
    license="MIT",
)
