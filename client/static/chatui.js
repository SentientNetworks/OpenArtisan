        // This is the main JS file for the Sentiet Chat program
        // It contains all the event handlers and utility functions

        var toolbarOptions = [[]]
        const textBox = document.getElementById("message");
        const addUserBox = document.getElementById("add_user");
        const modal = document.getElementById("modal-screen");
        const enterButton = document.getElementById("enter-button");
        const usernameInput = document.getElementById("username-input");
        const fileUploadButton = document.getElementById('file-upload');

        // The main central username - different for each client
        var CLIENT_USERNAME = "";

        var quill_chat_public = new Quill('#chat_public', {
            readOnly: true,
            modules: {
                toolbar: false,
            },            
            theme: 'snow'
        });

        var quill_chat_private = new Quill('#chat_private', {
            readOnly: true,
            modules: {
                toolbar: false,
            },
            theme: 'snow'
        });        

        var quill_users = new Quill('#users', {
            readOnly: true,
            modules: {
                toolbar: false,
            },            
            theme: 'snow'
        });

        // Utility Functions for printing the received message and updating the Quill editor windows

        function printMessage(username, sender, receiver, message, timestamp) {

            console.log("printMessage: timestamp = "+ timestamp);
            console.log("printMessage: username = " + username + ", sender = " + sender + ", receiver = " + receiver);

            if (receiver == CLIENT_USERNAME) {
                _printMessagePrivate(username, message, timestamp);
            }
            else if (message.includes("@")) {
                if (message.includes("@" + CLIENT_USERNAME)) {
                    _printMessagePrivate(username, message, timestamp);
                }
                else if (sender == CLIENT_USERNAME) {
                    _printMessagePrivate(username, message, timestamp);
                }
            }
            else {
                _printMessagePublic(username, message, timestamp);
            }

        }

        function _printMessagePublic(username, message, timestamp) {

            console.log("_printMessagePublic: timestamp = "+ timestamp);

            var length = quill_chat_public.getLength();

            quill_chat_public.insertText(length - 1, username + ' [' + timestamp + '] ' + ': ', {bold:true});

            length = quill_chat_public.getLength();

            if (message.includes(window.env.CODING_ID)) {
                quill_chat_public.clipboard.dangerouslyPasteHTML(length - 1, message + '<br><br><br>');
            }
            else {
                quill_chat_public.insertText(length - 1, message + '\n\n', {bold:false});
            }

        }

        function _printMessagePrivate(username, message, timestamp) {

            console.log("_printMessagePrivate: timestamp = "+ timestamp);

            var length = quill_chat_private.getLength();

            quill_chat_private.insertText(length - 1, username + ' [' + timestamp + '] ' + ': ', {bold:true});

            length = quill_chat_private.getLength();

            if (message.includes(window.env.CODING_ID)) {
                quill_chat_private.clipboard.dangerouslyPasteHTML(length - 1, message + '<br><br><br>');
            }
            else {
                quill_chat_private.insertText(length - 1, message + '\n\n', {bold:false});
            }

        }

        function clearChatQuill(userlist, current_username, visibility) {
            if (!userlist.includes(CLIENT_USERNAME)) {
                if (visibility == "public") {
                    quill_chat_public.setText("");
                }
                else if (visibility == "private") {
                    quill_chat_private.setText("");
                }
            }
        }

        function updateDropdowns(userlist, current_username) {

            const senders = document.getElementById("senders");
            senders.innerHTML = "";
            const receivers = document.getElementById("receivers");
            receivers.innerHTML = "";

            console.log(`adding ${CLIENT_USERNAME} to the dropdowns`);

            const option_room = document.createElement("option");
            option_room.value = "room";
            option_room.text = "Room";
            senders.appendChild(option_room);

            const option_ai = document.createElement("option");
            option_ai.value = "@AI";
            option_ai.text = "@AI";
            senders.appendChild(option_ai);

            const newOption = document.createElement("option");
            newOption.value = CLIENT_USERNAME;
            newOption.text = CLIENT_USERNAME;
            senders.appendChild(newOption);

            senders.selectedIndex = 2;

            console.log(`adding ${userlist} to the dropdowns`);

            const firstOption = document.createElement("option");
            firstOption.value = "room";
            firstOption.text = "Room";
            receivers.appendChild(firstOption);

            userlist.forEach(function(username) {
                if ((username != current_username) && (username != CLIENT_USERNAME)) {
                    const newOption = document.createElement("option");
                    newOption.value = username;
                    newOption.text = username;
                    receivers.appendChild(newOption);
                }
            });

            receivers.selectedIndex = 0;

        }

        function updateUserList(userlist, current_username) {

            if (!userlist.includes(current_username)) {
                userlist.push(current_username);
                console.log(`Added ${current_username} to the userlist ${userlist}.`);
            }

            console.log(`updating user list with ${current_username}`)
            updateDropdowns(userlist, current_username);
            
        }

        function leaveUserList(userlist, current_username) {

            if (userlist.includes(current_username)) {
                userlist.pop(current_username);
                console.log(`Removed ${current_username} from the userlist ${userlist}.`);
            }

            //clearChatQuill(userlist, current_username);
            //updateUsersQuill(userlist, current_username);

        }


        // The main document object once ready containing all the event handlers
        $(document).ready(function() {

        const socket = io();
        //let username = '';     
        
        //var isPrivate;
        let isPrivate = false;  // false = public view is showing

        $('#username').change(function() {
            
            username = $(this).val();

            socket.emit('join', {room: "room", username: username});
            
        });

        $('#toggle-public-private').click(function () {
            const public_screen = document.getElementById('public');
            const private_screen = document.getElementById('private');
            const button = document.getElementById('toggle-public-private');
            if (isPrivate) {
                public_screen.style.display = 'block';
                private_screen.style.display = 'none';
                button.textContent = 'Public';
            } else {
                public_screen.style.display = 'none';
                private_screen.style.display = 'block';
                button.textContent = 'Private';
            }

            isPrivate = !isPrivate;
        });        

        fileUploadButton.addEventListener('change', (event) => {
            const file = event.target.files[0];
            console.log(`file is ${file.data}`);
            const prompt = $('#message').val();
            if (file) {
              const reader = new FileReader();
              reader.onload = () => {
                const arrayBuffer = reader.result;
                //socket.send({type: 'file_upload', fileName: file.name, fileData: arrayBuffer });

                const message = {"filename": file.name, "filedata": arrayBuffer, "prompt": prompt};
                console.log(`inside fileUpload click: file name is ${file.name}`)
                const sender = document.getElementById('senders').value;
                const receiver = document.getElementById('receivers').value;
                const commands = document.getElementById('commands').value;
                console.log(`inside fileUpload click: commands is ${commands}`)
                const agentprompt = document.getElementById('agentprompt').value;
                console.log(`inside fileUpload click: agentprompt is ${agentprompt}`)
                sendMessage(message, sender, receiver, commands, agentprompt);
              };
              reader.readAsArrayBuffer(file);
              console.log(`inside fileUpload click: completed.`)
            }
        });        

        function sendMessage(message, sender, receiver, commands, agentprompt) {
            //document.getElementById('hourglass').style.display = 'block';
            console.log(`inside send click: sender is ${sender}`)
            socket.send({ type: 'message', username: CLIENT_USERNAME, message: message, sender: sender, receiver: receiver, commands: commands, agentprompt: agentprompt });
            $('#message').val('');
        }

        $('#send').click(function() {
            const message = $('#message').val();
            const commands = document.getElementById('commands').value;
            console.log(`inside send click: commands is ${commands}`)
            const agentprompt = document.getElementById('agentprompt').value;
            console.log(`inside send click: agentprompt is ${agentprompt}`)
            const sender = document.getElementById('senders').value;
            const receiver = document.getElementById('receivers').value;
            sendMessage(message, sender, receiver, commands, agentprompt);
        });

        textBox.addEventListener("keydown", function(event) {
            // Check if the 'Enter' key was pressed (key code 13)
            if (event.key === "Enter") {

                // Prevent the default form submit action
                event.preventDefault();

                const message = $('#message').val();
                const sender = document.getElementById('senders').value;
                const receiver = document.getElementById('receivers').value;
                const commands = document.getElementById('commands').value;
                console.log(`inside send enter: commands is ${commands}`)
                const agentprompt = document.getElementById('agentprompt').value;
                console.log(`inside send enter: agentprompt is ${agentprompt}`)
                sendMessage(message, sender, receiver, commands, agentprompt);
            }
        });

        // When the Enter button in the Enter modal is clicked, close the modal
        enterButton.addEventListener("click", function() {
            const in_username = document.getElementById("username-input").value;

            if (in_username) {
                modal.style.display = "none"; // Hide the modal
                $('#add_user').val(in_username); // Set username in the main input
                CLIENT_USERNAME = in_username
                socket.emit('message', {type: 'join', room: "room", username: CLIENT_USERNAME}); // Optionally send the username to the server
            }
        });            

        usernameInput.addEventListener("keydown", function(event) {
            // Check if the 'Enter' key was pressed (key code 13)
            if (event.key === "Enter") {
                // Prevent the default form submit action
                event.preventDefault();

                const in_username = document.getElementById("username-input").value;

                console.log(io.version);
                
                if (in_username) {
                    modal.style.display = "none"; // Hide the modal
                    $('#add_user').val(in_username); // Set username in the main input
                    CLIENT_USERNAME = in_username;
                    socket.emit('message', {type: 'join', room: "room", username: CLIENT_USERNAME}); // Optionally send the username to the server
                }
        }
        });

        $('#quit').click(function() {                        
            socket.send({ type: 'leave', username: CLIENT_USERNAME, room: 'room' });                
        });

        addUserBox.addEventListener("keydown", function(event) {
            // Check if the 'Enter' key was pressed (key code 13)
            if (event.key === "Enter") {
                // Prevent the default form submit action
                event.preventDefault();

                const tmp_username = $('add_user').val();
                const room = 'room';
                socket.emit('join', { username: tmp_username, room: room }, to=room);
                $('add_user').val('');
            }
        });

        function isObject(value) {
           return typeof value === 'object' && value !== null && !Array.isArray(value);
        }        

        // Handler for the message event from the server
        // We are now using the event for all message types since this seems to work
        socket.on('message', function(data) {

            const in_username = document.getElementById("username-input").value;

            if (('type' in data) && (data.type == 'join')) {
                console.log("updating user list after broadcast of join "+data.userlist+" "+data.username)
                updateUserList(data.userlist, CLIENT_USERNAME);
            }
            else if (('type' in data) && (data.type == 'leave')) {
                console.log("updating user list after broadcast of leave "+data.userlist+" "+data.username)
                leaveUserList(data.userlist, data.username);                
                clearChatQuill(data.userlist, data.username, "public");
                clearChatQuill(data.userlist, data.username, "private");
                quill_image.setContents([]);
                windowElement.style.display = 'none';

                // Reshow the modal if this is the client for the user that left
                if (data.username == CLIENT_USERNAME) {
                    modal.style.class = 'modal';
                    modal.style.position = 'fixed';
                    modal.style.zIndex = 1000; /* Sits on top of the rest of the page */
                    modal.style.left = 0;
                    modal.style.top = 0;
                    modal.style.width = '100%';
                    modal.style.height =  '100%';
                    modal.style.backgroundColor = "rgba(0, 0, 0, 0.5)"; /* Semi-transparent background */
                    modal.style.justifyContent = 'center';
                    modal.style.alignItems = 'center';
                    modal.style.display = 'block';
                    modal.style.display = 'flex';
                }
            }
            else if (('type' in data) && (data.type == 'connect')) {
                console.log("updating user list after broadcast of connect "+data.userlist+" "+data.username)
                updateUserList(data.userlist, CLIENT_USERNAME);
            }                
            else if (('type' in data) && (data.type == 'disconnect')) {
                console.log("updating user list after broadcast of disconnect "+data.userlist+" "+data.username)
                leaveUserList(data.userlist, CLIENT_USERNAME);
            }                
            else {

                if (isObject(data.message.content)) {
                    content = JSON.stringify(data.message.content)
                }
                else {
                    content = data.message.content;
                }

                printed_content = content.substring(0, 20);

                console.log("This is a general message from "+data.username+" with content "+printed_content+" "+typeof content)

                if (data.undo_hourglass == "true") {
                    document.getElementById('hourglass').style.display = 'none';
                }
                
                printMessage(data.username, data.sender, data.receiver, content, data.timestamp);
            }

        });

        var quill_image = new Quill('#imagemessage', {
            readOnly: true,
            modules: {
                toolbar: false,
            },            
            theme: 'snow'
        });

        socket.on('image_message', (data) => {

            if (data.undo_hourglass == "true") {
                    document.getElementById('hourglass').style.display = 'none';
            }

            quill_image.setContents([]);
            var length = quill_image.getLength();
            quill_image.clipboard.dangerouslyPasteHTML(length - 1, data.message.content + '<br><br><br>');

            const windowElement = document.getElementById('myWindow');
            windowElement.style.display = 'flex';

            messagesDiv.appendChild(messageElement);
        });


        socket.on("connect_error", (err) => {
            // the reason of the error, for example "xhr poll error"
            console.log(err.message);

            // some additional description, for example the status code of the initial HTTP response
            console.log(err.description);

            // some additional context, for example the XMLHttpRequest object
            console.log(err.context);
        });

        // Handler for the join event not used now
        // Instead the join message is sent to the message event handled above
        socket.on('join', function(data) {

            const in_username = document.getElementById("username-input").value;

            if (('type' in data) && (data.type == 'join')) {
                console.log("updating user list after broadcast of join "+data.userlist+" "+data.username)
                updateUserList(data.userlist, data.username);
            }

        }); 

        socket.on('error', (data) => {
            console.error(data.msg);
        });            

        });

        document.getElementById('toggle-textarea').addEventListener('click', function() {
            const commands = document.getElementById('commands');
            const agentprompt = document.getElementById('agentprompt');
            if (commands.style.display === 'none') {
                commands.style.display = 'block';
                agentprompt.style.display = 'none';
            } else {
                commands.style.display = 'none';
                agentprompt.style.display = 'block';
            }
        });
