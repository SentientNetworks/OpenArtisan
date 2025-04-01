import os, sys
import time

def contains_directory(parent_dir, sub_dir = None):

	if not os.path.isdir(parent_dir):
		return False

	if sub_dir is None:
		return True

	# Create the full path of the subdirectory
	sub_dir_path = os.path.join(parent_dir, sub_dir)
    
	# Check if the path exists and is a directory
	if os.path.isdir(sub_dir_path):
		return True
	else:
		return False

def create_directory(parent_dir, new_dir):

	# Create the new directory
	try:
		dir_path = os.path.join(parent_dir, new_dir)

		os.makedirs(dir_path)
		print(f'Directory {new_dir} created successfully in {parent_dir}')
	except OSError as error:
		print(f'Error creating directory: {error}')
		return False

	return True

def file_exists(home_dir, function_name, file_name):

	try: 
		file_path = os.path.join(home_dir, function_name, file_name)

		if os.path.exists(file_path):
			print(f"FileManager::file_exists: The file {file_path} exists.")
			return True
		else:
			print(f"FileManager::file_exists: The file {file_path} does not exist.")
			return False
	except Exception as e:
		print(f"FileManager::file_exists: Error for file {file_path} with exception {e}.")
		return False

	return True

def generate_unique_filename(prefix, suffix):

	current_time = time.time()

	return f"{prefix}_{current_time}.{suffix}"


def create_file(functions_directory, functionname, script_filename, content):

	try:
		file_path = os.path.join(functions_directory, functionname, script_filename)

		# Open a file in write mode
		with open(file_path, 'w') as file:
			# Write content to the file
			file.write(content)

		print("FileManager::create_file: File created and content written successfully.")
	except Exception as e:
		print("FileManager::create_file: File created and content writing failed.")
		return False

	return True