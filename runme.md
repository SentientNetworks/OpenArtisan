There are five servers to run.

First time:
-----------
Create a base directory <BASE_DIR>
unzip the source files into this directory or do a git clone.
run pip install -r requirements in a command prompt 
Its not too bad only 6 packages to install.


To run:
------
Change directory to <BASE_DIR>

Running the engine:

load a command prompt in an environment containing python

You will need to set the organization and OPENAI_API_KEY environment variables
You can use your OpenAI account or create one.

Set the CODING_ID environment variable to the value provided

cd engine
python engine.py


Running the functions server:

load a command prompt in an environment containing python

cd functions
python functionserver.py


Running the memory server:

load a command prompt in an environment containing python

cd memory
python memoryserver.py


Running the messaging server:

load a command prompt in an environment containing python

cd messaging
python messageserver.py


Running the sample client:

load a command prompt in an environment containing python

Set the CODING_ID environment variable to the value provided
This must be the same as the value of the CODING_ID environment variable
set when running the engine.

cd client
python clientserver.py

You can now access the client at http://localhost:5000/.

