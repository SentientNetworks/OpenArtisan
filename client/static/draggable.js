        // Draggable Function
        function makeDraggable(element) {
        let posX = 0, posY = 0, mouseX = 0, mouseY = 0;
        const header = element.querySelector('.window-header');

        header.onmousedown = dragMouseDown;

        function dragMouseDown(e) {
            e.preventDefault();
            mouseX = e.clientX;
            mouseY = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }

        function elementDrag(e) {
            e.preventDefault();
            posX = mouseX - e.clientX;
            posY = mouseY - e.clientY;
            mouseX = e.clientX;
            mouseY = e.clientY;
            element.style.top = (element.offsetTop - posY) + "px";
            element.style.left = (element.offsetLeft - posX) + "px";
        }

        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
        }

        const minimizeBtn = document.querySelector('.window-minimize');
        const windowContent = document.querySelector('.window-content');
        const windowElement = document.getElementById('myWindow');

        minimizeBtn.addEventListener('click', () => {
        if (windowContent.style.display === 'none') {
            windowContent.style.display = 'block';
            windowElement.style.height = '300px'; // Reset to original height
            windowElement.style.width = '400px'; // Reset to original width
        } else {
            windowContent.style.display = 'none';
            windowElement.style.height = 'auto'; // Adjust height when minimized
            windowElement.style.width = 'auto'; // Adjust width when minimized
        }
        });

        const closeBtn = document.querySelector('.window-close');

        closeBtn.addEventListener('click', () => {
        windowElement.style.display = 'none';
        });



        // Apply to your window
        makeDraggable(document.getElementById('myWindow'));

        windowElement.style.display = 'none';
