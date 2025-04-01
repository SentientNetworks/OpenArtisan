        // This is the main JS file for the Sentiet Chat program
        // It contains all the event handlers and utility functions

        var toolbarOptions = [[]]
        const textBox = document.getElementById("message");
        const addUserBox = document.getElementById("add_user");
        const modal = document.getElementById("modal-screen");
        const enterButton = document.getElementById("enter-button");
        const usernameInput = document.getElementById("username-input");

        // The main central username - different for each client
        var CLIENT_USERNAME = "";

        var quill_chat = new Quill('#chat', {
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

        function printMessage(username, message) {

            var length = quill_chat.getLength();

            quill_chat.insertText(length - 1, username + ': ', {bold:true});

            length = quill_chat.getLength();

            if (message.includes(window.env.CODING_ID)) {
                quill_chat.clipboard.dangerouslyPasteHTML(length - 1, message + '<br><br><br>');
            }
            else {
                quill_chat.insertText(length - 1, message + '\n\n', {bold:false});
            }

        }

        function updateUsersQuill(userlist, current_username) {

            quill_users.setText('');
            quill_users.insertText(0, 'Users\n\n', {bold:true})
            userlist.forEach(function(username) {
                
                var length = quill_users.getLength();
                var format = {bold:false}

                if ((current_username == username) || (username == CLIENT_USERNAME)) {
                    format = {bold:true}
                }

                quill_users.insertText(length - 1, username + '\n', format);                                

            });

        }

        function clearChatQuill(userlist, current_username) {
            if (!userlist.includes(CLIENT_USERNAME)) {
                quill_chat.setText("");
            }

            updateUsersQuill(userlist, current_username);
        }

        function updateUserList(userlist, current_username) {

            if (!userlist.includes(current_username)) {
                userlist.push(current_username);
                console.log(`Added ${current_username} to the userlist ${userlist}.`);
            }

            updateUsersQuill(userlist, current_username);
            
        }

        function leaveUserList(userlist, current_username) {

            if (userlist.includes(current_username)) {
                userlist.pop(current_username);
                console.log(`Removed ${current_username} from the userlist ${userlist}.`);
            }

            //clearChatQuill(userlist, current_username);
            updateUsersQuill(userlist, current_username);

        }

        // The main document object once ready containing all the event handlers
        $(document).ready(function() {

        const socket = io();
        //let username = '';           

        $('#username').change(function() {
            
            username = $(this).val();

            socket.emit('join', {room: "room", username: username});
            
        });

        function sendMessage(message, sender, receiver, commands) {
            //document.getElementById('hourglass').style.display = 'block';
            console.log(`inside send click: sender is ${sender}`)
            socket.send({ type: 'message', username: CLIENT_USERNAME, message: message, sender: sender, receiver: receiver, commands: commands });
            $('#message').val('');
        }

        $('#send').click(function() {
            const message = $('#message').val();
            const commands = document.getElementById('commands').value;
            console.log(`inside send click: commands is ${commands}`)            
            const sender = CLIENT_USERNAME;
            const receiver = "room";
            sendMessage(message, sender, receiver, commands)
        });

        textBox.addEventListener("keydown", function(event) {
            // Check if the 'Enter' key was pressed (key code 13)
            if (event.key === "Enter") {

                // Prevent the default form submit action
                event.preventDefault();

                const message = $('#message').val();
                const commands = document.getElementById('commands').value;
                console.log(`inside send click: commands is ${commands}`)                
                const sender = CLIENT_USERNAME;
                const receiver = "room";
                sendMessage(message, sender, receiver, commands)

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
                clearChatQuill(data.userlist, data.username);
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
                console.log("This is a general message from "+data.username+" with content "+data.message.content)

                if (data.undo_hourglass == "true") {
                    document.getElementById('hourglass').style.display = 'none';
                }

                printMessage(data.username, data.message.content);
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
