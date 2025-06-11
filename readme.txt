Artisan
=======

Artisan is a server side system to handle and augment AI communication.
It was written to be a base for testing certain ideas with regard to AI.
This now includes testing the nature of LLMs as a function.

Description
-----------

Artisan at runtime consists of five servers:

Message Server (routes messages in the system including the client)
Engine Server (wraps communication with AI implementations)
Memory Server (allows for use of external database resources if needed)
Functions (or Tools) Server (allows the AI to create and run code including external systems)
Timer Server (allows for prodding of the AI to get it to do things periodically)

Memory, Functions and Timer are works in progress.


Installation and Running the System
-----------------------------------

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


Running the timer server:

load a command prompt in an environment containing python

cd timer
python timerserver.py


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


The engine, functions and client (not mentioned here) require some environment variables to be set up.

You can now access the client at http://localhost:5000/.

