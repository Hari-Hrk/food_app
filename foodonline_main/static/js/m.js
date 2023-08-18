const accessTokens = 'pk.eyJ1IjoiaGFyaXNoODciLCJhIjoiY2xsZW80ODdrMDVhbjNqcWo0NnVrY2lveiJ9.XSIIObQnlVfMBdA6qpYtaA';
//const addressInput = document.getElementById('#id_address');
//const suggestionsList = document.getElementById('suggestions-list');


document.addEventListener('DOMContentLoaded', function() {
    const accessToken = accessTokens
    const addressInput = document.getElementById('id_address');
    const suggestionsList = document.getElementById('suggestions-list');

    addressInput.addEventListener('input', handleInput);

    function handleInput() {
        const query = addressInput.value;

        if (query.length >= 2) {
            getSuggestions(query)
                .then(suggestions => displaySuggestions(suggestions));
        } else {
            clearSuggestions();
        }
    }

    async function getSuggestions(query) {
        const response = await fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${query}.json?access_token=${accessToken}`);
        const data = await response.json();
        return data.features;
    }

    function displaySuggestions(suggestions) {
        clearSuggestions();

        for (const suggestion of suggestions) {
            const listItem = document.createElement('li');
            listItem.textContent = suggestion.place_name;
            listItem.addEventListener('click', () => selectAddress(suggestion));
            suggestionsList.appendChild(listItem);
        }
    }

    function clearSuggestions() {
        suggestionsList.innerHTML = '';
    }

    function selectAddress(address) {
        addressInput.value = address.place_name;

        const addressComponents = address.place_name.split(', ');
        const city = addressComponents[addressComponents.length - 3];
        const regex = /([a-zA-Z ]+) (\d+)/;
        const matches = addressComponents[addressComponents.length - 2].match(regex);
        let state = "";
        let pincode = "";
        if (matches && matches.length >= 3) {
             state = matches[1].trim();
             pincode = matches[2].trim();        
        }
        
        const country = addressComponents[addressComponents.length - 1];
        const latitude = address.geometry.coordinates[1];
        const longitude = address.geometry.coordinates[0];
        $('#id_city').val(city);
        $('#id_state').val(state);
        $('#id_pincode').val(pincode);
        $('#id_country').val(country);
        $('#id_latitude').val(latitude);
        $('#id_longitude').val(longitude);
        
        clearSuggestions();
    }
});