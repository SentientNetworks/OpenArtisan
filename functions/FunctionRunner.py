import os, sys
import json
import subprocess
from FileManager import contains_directory, create_directory, file_exists, generate_unique_filename, create_file

class CFunctionRunner:

    def __init__(self, config):
        self.configurator = config
        self.functions_directory = os.getenv("FUNCTIONS_DIRECTORY")
        self.sandbox_command = os.getenv("SANDBOX_COMMAND")
		
    def prepare(self, message):

        print(f"CFunctionRunner::prepare: entered method")

        if not contains_directory(self.functions_directory):
            print(f"CFunctionRunner::prepare functions directory does not exist")
            return None, False
        
        try:
            print(f"CFunctionRunner::prepare starting preparation")

            dMessage = json.loads(message)

            if type(dMessage["content"]) is str:
                dContent = json.loads(dMessage["content"])
            else:
                dContent = dMessage["content"]
            
            inline = False
            if dContent["type"] == "inline":
                inline = True
            details = dContent["functions"]
            newDetails = details

            if inline:

                for function in newDetails:

                    if function["name"] == "inline":

                        script = function["script"]

                        script_filename = generate_unique_filename("script_", ".py")

                        if not contains_directory(self.functions_directory, sub_dir=function["name"]):
                            print(f"CFunctionRunner::prepare functions functionname directory does not exist")
                            if not create_directory(self.functions_directory, function["name"]):
                                print(f"CFunctionRunner::prepare creating functions functionname directory failed")
                                return None, False

                        if create_file(self.functions_directory, function["name"], script_filename, script):
                            print(f"CFunctionRunner::prepare creating inline script file failed")
                            function["script"] = script_filename

                details = newDetails

                # test the function name
                # check if functions_directory\functionname exists
                # if not create it

                # generate the unique script file
                # create the file and write the contents of function["script"] into it

        except Exception as e:
            print(f"CFunctionRunner::prepare failed with exception {e}")
            return None, False

        return details, True

    def run(self, details):

        print(f"CFunctionRunner::run: entered method")

        # return output
        output = []
        scriptFile = "script.py"

        for function in details:

            functionName = function["name"]
            parameters = ""

            if "script" in function and len(function["script"]) > 0:
                scriptFile = function["script"]

            if "parameters" in function:
                parameters = function["parameters"]

            inputString = ""
            if type(parameters) is list:
                inputString = str(parameters)
            elif len(parameters) > 0:
                inputString = str([parameters])
            else:
                inputString = str([])

            # If the function name does not exist as a directory in the main functions directory
            # then we return None for now
            # In the future we may create a directory

            if not contains_directory(self.functions_directory, sub_dir=functionName):
                print(f"CFunctionRunner::run: function {functionName} does not exist in {self.functions_directory}")
                return None
            
            # Now check that the file script.py file exists in the location
            # For now leave with None if it is not there but in the  future we create the file

            if not file_exists(self.functions_directory, functionName, scriptFile):
                print(f"CFunctionRunner::run: directory {functionName} does not have a file {scriptFile}")
                return None
            
            outputString = self.runScript(self.functions_directory, functionName, scriptFile, inputString)  

            output.append({"name": functionName, "output": outputString})        

            # for now we only allow one function to be called until we work out how to do this
            break  

        return output
        
    def respond(self, message, output, details):

        print(f"CFunctionRunner::respond: entered method")

        try:
            dMessage = json.loads(message)
            payload = {"functions_output": output}
            dMessage["content"] = payload
            message = json.dumps(dMessage)

        except Exception as e:
            print(f"CFunctionRunner::respond: exception {e}")
            return message

        return message
    
    def runScript(self, home_dir, function_name, script_file, input_string):

        output, error = self.run_sandbox(home_dir, function_name, script_file, input_string)

        if error is not None and len(error) > 0:
            return error
        else:
            return output

        return None
    
    def run_sandbox(self, functionsDir, functionName, scriptFile, input_data):

        try:
            scriptPath = os.path.join(functionsDir, functionName, scriptFile)

            sandbox_process = subprocess.Popen(
                [self.sandbox_command, '--', scriptPath],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = sandbox_process.communicate(input=input_data)
        except Exception as e:
            print(f"CFunctionRunner::run_sandbox: error {e}")
            return None, None
    
        return stdout, stderr
