function fetchImages() {
    const accessToken = localStorage.getItem('access_token');
    if (!accessToken) {
        alert('You are not logged in. Please log in to view images.');
        window.location.href = '/login';
        return;
    }

    fetch('/get_images', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${accessToken}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        const imagesContainer = document.getElementById('userImages');
        imagesContainer.innerHTML = '';

        if (data.success && data.images.length > 0) {
            data.images.forEach(imageUrl => {
                const imgElement = document.createElement('img');
                imgElement.src = imageUrl;
                imgElement.style.width = '90%'; // Default size
                imgElement.style.marginBottom = '10px';
                imgElement.classList.add('image-item');
                imgElement.addEventListener('click', () => {
                    imgElement.classList.toggle('selected');
                    if (imgElement.classList.contains('selected')) {
                        imgElement.style.width = '100%'; // Make the image slightly bigger when selected
                    } else {
                        imgElement.style.width = '90%'; // Revert to default size when deselected
                    }
                });
                imagesContainer.appendChild(imgElement);
            });
        } else {
            imagesContainer.innerHTML = 'No images to display';
        }
    })
    .catch(error => {
        console.error('Error fetching images:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {

    const accessToken = localStorage.getItem('access_token');

    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignUp);
    }

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');
    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', function() {
            uploadFile(this.files[0]);
        });
    }

    function handleSignUp(event) {
        event.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (password !== confirmPassword) {
            alert('Passwords do not match!');
            return;
        }

        fetch('/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Signup successful!');
                window.location.href = '/login';
            } else {
                alert('Signup failed: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again later.');
        });
    }

    function handleLogin(event) {
        event.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Login successful.');
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('loggedInUser', username);
                window.location.href = '/';
            } else {
                alert('Invalid credentials. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again later.');
        });
    }

    const dragDropBox = document.getElementById('dragDropBox');
    if (dragDropBox && fileInput) {
        dragDropBox.addEventListener('click', () => fileInput.click());

        dragDropBox.addEventListener('dragover', (event) => {
            event.stopPropagation();
            event.preventDefault();
            event.dataTransfer.dropEffect = 'copy'; // visually indicate that this is a copy action
        });

        dragDropBox.addEventListener('drop', (event) => {
            event.stopPropagation();
            event.preventDefault();
            const files = event.dataTransfer.files;
            if (files.length) {
                uploadFile(files[0]);
            }
        });
    }

    function uploadFile(file) {
        if (!allowed_file(file.name)) {
            alert('Invalid file type. Only JPG, JPEG, and PNG are allowed.');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload', {
            method: 'POST',
            body: formData,
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Image uploaded successfully');
                console.log('Image URL:', data.image_url);
            } else {
                alert('Upload failed: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred during upload. Please try again later.');
        });
    }

    function allowed_file(filename) {
        return /\.(jpg|jpeg|png)$/i.test(filename);
    }
    if (window.location.pathname === '/') {
        checkLoggedIn();
    }

    function checkLoggedIn() {
        const loggedInUser = localStorage.getItem('loggedInUser');
        if (loggedInUser) {
            document.getElementById('loginSection').style.display = 'none';
            document.getElementById('loggedInSection').style.display = 'block';
            document.getElementById('loggedInUsername').textContent = loggedInUser;
            document.getElementById('logoutBtn').style.display = 'block';
        } else {
            document.getElementById('loginSection').style.display = 'block';
            document.getElementById('loggedInSection').style.display = 'none';
            document.getElementById('logoutBtn').style.display = 'none';
        }
    }

    const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', function() {
        localStorage.removeItem('loggedInUser');
        localStorage.removeItem('access_token');
        checkLoggedIn();
        window.location.href = '/';
    });
}

    const pathname = window.location.pathname;
    if (pathname.includes('/video')) {
        fetchImages();

        const createVideoBtn = document.getElementById('createVideoBtn');
        if (createVideoBtn){
            document.getElementById('createVideoBtn').addEventListener('click', function() {
                const selectedImages = document.querySelectorAll('.image-item.selected');
                const imageUrls = Array.from(selectedImages).map(img => img.src);
                console.log('Selected image URLs:', imageUrls);
                const resolution = document.getElementById('resolution').value;
                const audioMood = document.getElementById('audioMood').value;
                
                console.log("Selected resolution:",resolution);
                console.log("Selected audio:",audioMood);
                // Send data to the server to create the video
                fetch('/create_video', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ imageUrls, resolution, audioMood })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('videoPreview').src = data.videoUrl;
                        const downloadLink = document.getElementById('downloadVideo');
                        downloadLink.href = data.videoUrl;
                        downloadLink.style.display = 'block';
                        downloadLink.download = 'YourVideo.mp4';
                    } else {
                        alert('Failed to create video');
                    }
                })
                .catch(error => {
                    console.error('Error creating video:', error);
                });
            });
        
        }
    }
});





