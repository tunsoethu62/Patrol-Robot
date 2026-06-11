from setuptools import find_packages, setup

package_name = 'patrol_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/patrol_pkg/launch', ['launch/world_test.launch.py']),
        ('share/patrol_pkg/worlds', ['worlds/world_test.world']),
        ('share/patrol_pkg/rviz', ['rviz/patrol_config.rviz'])
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='soethutun',
    maintainer_email='soethutun@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'my_node = patrol_pkg.my_node:main',
            'sensor_node = patrol_pkg.sensor_node:main',
            'controller_node = patrol_pkg.controller_node:main',
            'monitor_node = patrol_pkg.monitor_node:main',
            'virtual_sensor_tf = patrol_pkg.virtual_sensor_tf:main'
        ],
    },
)
