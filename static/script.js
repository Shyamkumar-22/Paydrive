// Utility to show error messages
function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
    } else {
        console.error(`Error element ${elementId} not found`);
    }
}

// Initialize district autocomplete for a given input and options element
function initializeDistrictAutocomplete(inputId, optionsId) {
    const input = document.getElementById(inputId);
    const options = document.getElementById(optionsId);
    if (!input || !options) {
        console.error(`Input (${inputId}) or options (${optionsId}) element not found`);
        return;
    }

    console.log(`Initializing district autocomplete for ${inputId}`);
    const districts = [
        'Chennai', 'Coimbatore', 'Madurai', 'Tiruchirappalli', 'Salem',
        'Tirunelveli', 'Erode', 'Vellore', 'Thoothukudi', 'Dindigul',
        'Thanjavur', 'Karur', 'Namakkal', 'Nilgiris', 'Kanyakumari'
    ];

    const updateDistrictOptions = (filter = '') => {
        options.innerHTML = '';
        const filteredDistricts = districts.filter(district =>
            district.toLowerCase().includes(filter.toLowerCase())
        );
        if (filteredDistricts.length === 0) {
            options.classList.add('hidden');
            return;
        }
        filteredDistricts.forEach(district => {
            const li = document.createElement('li');
            li.className = 'px-4 py-2 hover:bg-blue-100 cursor-pointer';
            li.textContent = district;
            li.addEventListener('click', () => {
                input.value = district;
                options.classList.add('hidden');
            });
            options.appendChild(li);
        });
        options.classList.remove('hidden');
    };

    updateDistrictOptions();

    input.addEventListener('input', () => {
        const filter = input.value.trim();
        updateDistrictOptions(filter);
    });

    input.addEventListener('focus', () => {
        updateDistrictOptions(input.value.trim());
    });

    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !options.contains(e.target)) {
            options.classList.add('hidden');
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Clear rides list on page load to prevent stale data (for ride_request.html)
    const rideList = document.getElementById('rides-list');
    if (rideList) {
        rideList.innerHTML = '';
    }

    // Initialize district autocomplete for all relevant pages
    initializeDistrictAutocomplete('district-search', 'district-options'); // choose.html
    initializeDistrictAutocomplete('search-location', 'search-location-options'); // ride_request.html
    initializeDistrictAutocomplete('offer-location', 'offer-location-options'); // ride_offer.html

    // Profile form submission (profile.html)
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(profileForm);

            const requiredFields = ['name', 'email', 'phone', 'dob', 'gender', 'language'];
            for (const field of requiredFields) {
                if (!formData.get(field)) {
                    showError('profile-error', 'All fields except emergency contact and picture are required');
                    return;
                }
            }

            try {
                const response = await fetch('/profile', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (response.ok) {
                    alert(result.message || 'Profile saved successfully!');
                    window.location.href = '/choose';
                } else {
                    showError('profile-error', result.error || 'Error saving profile');
                }
            } catch (error) {
                showError('profile-error', 'An error occurred. Please try again.');
                console.error('Profile error:', error);
            }
        });
    }

    // Login functionality (index.html)
    const loginButton = document.getElementById('login-button');
    if (loginButton) {
        console.log('Login button found, attaching event listener');
        loginButton.addEventListener('click', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username')?.value;
            const password = document.getElementById('password')?.value;

            if (!username || !password) {
                showError('login-error', 'Username and password are required');
                return;
            }

            try {
                console.log('Submitting login to /login with username:', username);
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ username, password })
                });
                const data = await response.json();
                console.log('Login response:', data);

                if (response.ok) {
                    sessionStorage.setItem('username', username);
                    console.log('Login successful, redirecting to:', data.redirect);
                    window.location.href = data.redirect;
                } else {
                    showError('login-error', data.error || 'Invalid username or password');
                }
            } catch (error) {
                showError('login-error', 'An error occurred. Please try again.');
                console.error('Login error:', error);
            }
        });
    }

    // Signup functionality (signup.html)
    const signupButton = document.getElementById('signup-button');
    if (signupButton) {
        console.log('Signup button found, attaching event listener');
        signupButton.addEventListener('click', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username')?.value;
            const password = document.getElementById('password')?.value;

            if (!username || !password) {
                showError('signup-error', 'Username and password are required');
                return;
            }

            try {
                console.log('Submitting signup to /signup with username:', username);
                const response = await fetch('/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: new URLSearchParams({ username, password })
                });
                const data = await response.json();
                console.log('Signup response:', data);

                if (response.ok) {
                    sessionStorage.setItem('username', username);
                    console.log('Signup successful, redirecting to /');
                    window.location.href = data.redirect;
                } else {
                    showError('signup-error', data.error || 'Username already exists');
                }
            } catch (error) {
                showError('signup-error', 'An error occurred. Please try again.');
                console.error('Signup error:', error);
            }
        });
    }

    // Ride offer submission (ride_offer.html)
    const offerForm = document.getElementById('submit-offer');
    if (offerForm) {
        const backButton = document.getElementById('back-to-choose');
        if (backButton) {
            backButton.addEventListener('click', () => {
                console.log('Back button clicked, redirecting to /choose');
                window.location.href = '/choose';
            });
        }

        offerForm.addEventListener('click', async (e) => {
            e.preventDefault();
            const offerData = {
                address: document.getElementById('offer-address')?.value,
                location: document.getElementById('offer-location')?.value,
                arrival_time: document.getElementById('offer-arrival')?.value,
                frequent: document.getElementById('offer-frequent')?.value,
                bike_name: document.getElementById('offer-bike-name')?.value,
                gender: document.getElementById('offer-gender')?.value,
                phone: document.getElementById('offer-phone')?.value,
                bike_model: document.getElementById('offer-bike-model')?.value,
                licence: document.getElementById('offer-licence')?.value,
                bike_color: document.getElementById('offer-bike-color')?.value,
                bike_number: document.getElementById('offer-bike-number')?.value
            };

            if (!Object.values(offerData).every(val => val)) {
                showError('offer-error', 'All fields are required');
                return;
            }

            try {
                const response = await fetch('/offer_ride', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(offerData)
                });
                const data = await response.json();

                if (response.ok) {
                    alert(data.message || 'Ride offer submitted successfully!');
                    window.location.href = data.redirect;
                } else {
                    showError('offer-error', data.error || 'Error submitting offer');
                }
            } catch (error) {
                showError('offer-error', 'An error occurred. Please try again.');
                console.error('Offer error:', error);
            }
        });
    }

    // Ride request functionality (ride_request.html)
    const searchButton = document.getElementById('search-rides');
    if (searchButton) {
        console.log('Search rides button found, attaching event listener');
        const backButton = document.getElementById('back-to-choose');
        if (backButton) {
            backButton.addEventListener('click', () => {
                console.log('Back button clicked, redirecting to /choose');
                window.location.href = '/choose';
            });
        }

        searchButton.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log('Search rides button clicked');
            const location = document.getElementById('search-location')?.value?.trim();

            if (!location) {
                showError('search-error', 'Please enter a location');
                console.log('Location input empty');
                return;
            }

            try {
                console.log('Fetching rides from /search_rides with location:', location);
                const response = await fetch(`/search_rides?location=${encodeURIComponent(location)}`);
                const rides = await response.json();
                console.log('Search rides response:', rides);

                const rideList = document.getElementById('rides-list');
                if (rideList) {
                    rideList.innerHTML = '';
                    if (!response.ok) {
                        showError('search-error', rides.error || 'Error fetching rides');
                        console.log('Search rides failed:', rides.error);
                        return;
                    }

                    if (rides.length === 0) {
                        rideList.innerHTML = '<p class="text-gray-500">No rides available.</p>';
                        console.log('No rides found for location:', location);
                        return;
                    }

                    rides.forEach(ride => {
                        const rideCard = document.createElement('div');
                        rideCard.className = 'ride-card bg-gray-100 p-4 rounded-lg mb-4';
                        rideCard.innerHTML = `
                            <p><strong>Name:</strong> ${ride.name}</p>
                            <p><strong>Location:</strong> ${ride.location}</p>
                            <p><strong>Arrival Time:</strong> ${new Date(ride.arrival_time).toLocaleString()}</p>
                            <p><strong>Bike:</strong> ${ride.bike_name} (${ride.bike_model}, ${ride.bike_color}, ${ride.bike_number})</p>
                            <p><strong>Gender:</strong> ${ride.gender}</p>
                            <p><strong>Phone:</strong> ${ride.phone}</p>
                            <p><strong>License No:</strong> ${ride.licence}</p>
                            <button class="request-ride bg-blue-500 text-white px-4 py-2 rounded-lg mt-2 hover:bg-blue-600" data-id="${ride.id}">Request Ride</button>
                        `;
                        rideList.appendChild(rideCard);
                    });

                    console.log('Rides displayed, attaching request-ride listeners');
                    document.querySelectorAll('.request-ride').forEach(button => {
                        button.addEventListener('click', async (e) => {
                            e.preventDefault();
                            const rideId = e.target.dataset.id;
                            console.log('Request ride button clicked for ride ID:', rideId);

                            try {
                                const form = document.createElement('form');
                                form.method = 'POST';
                                form.action = '/request_ride';
                                form.innerHTML = `
                                    <input type="hidden" name="ride_id" value="${rideId}">
                                `;
                                document.body.appendChild(form);
                                console.log('Submitting form to /request_ride');
                                form.submit();
                            } catch (error) {
                                showError('search-error', 'An error occurred. Please try again.');
                                console.error('Request ride error:', error);
                            }
                        });
                    });
                } else {
                    console.error('rides-list element not found');
                }
            } catch (error) {
                showError('search-error', 'Error fetching rides. Please try again.');
                console.error('Search rides error:', error);
            }
        });
    }
});