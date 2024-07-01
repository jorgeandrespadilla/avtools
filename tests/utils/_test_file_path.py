from avtools.utils import FilePath


try:
    file_path = FilePath('test.py')

    # Properties
    print("Full Path:", file_path.full_path)
    print("Directory Path:", file_path.directory_path)
    print("Full Name:", file_path.full_name)
    print("Base Name:", file_path.base_name)
    print("File Extension:", file_path.extension)
    print("File Extension Without Dot:", file_path.extension_without_dot)

    # Validation Methods
    print("File Exists:", file_path.file_exists())
    print("Directory Exists:", file_path.directory_exists())

    # Path Manipulation Methods
    print("With Full Name:", file_path.with_full_name('test.txt'))
    print("With Base Name:", file_path.with_base_name('test'))
    print("With Extension:", file_path.with_extension('.txt'))

    # Other
    print("New File with Same Directory:", FilePath(
        file_path.directory_path / 'new_file.py'))
    print("New File with Nested Directory:", FilePath(
        file_path.directory_path / 'nested' / 'new_file.py'))
    print("Sample File with Nested Directory:", FilePath(
        file_path.directory_path / 'nested' / file_path.full_name))
except ValueError as e:
    print(f"Validation error: {e}")
