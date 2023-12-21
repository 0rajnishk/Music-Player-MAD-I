var $visualizers = $('.visualizer>div');
var $progressBar = $('.progress-bar');
var $progressBarRunner = $progressBar.find('.runner');
var percentage = 0;
var $time = $('.time');
var footer = document.getElementById('song-footer');
const timeElement = document.querySelector('.time');
var $player = $('.player');
var $audioPlayer = $('#audioPlayer')[0]; // Get the raw DOM element
var songCloseButton = document.getElementById('song-footer-close');


var playRunner = null;
var songLength;

// Function to handle loadedmetadata event
function handleMetadata() {
    songLength = $audioPlayer.duration;
    timeElement.textContent = (songLength / 60).toFixed(0) + ':' + (songLength % 60).toFixed(0);
}
document.addEventListener('DOMContentLoaded', function () {
    handleMetadata();
});


// Add an event listener for loadedmetadata to call handleMetadata when the audio loads
$audioPlayer.addEventListener('loadedmetadata', handleMetadata);

// Add an event listener for timeupdate
$audioPlayer.addEventListener('timeupdate', function () {
    if (!$audioPlayer.paused) {
        percentage = ($audioPlayer.currentTime / $audioPlayer.duration) * 100;
        $progressBarRunner.css('width', percentage + '%');
        $time.text(calculateTime($audioPlayer.duration, percentage));
    }
});

// Add an event listener for ended to clear the interval when the audio ends
$audioPlayer.addEventListener('ended', function () {
    clearInterval(playRunner);
    $player.toggleClass('paused').toggleClass('playing');
    percentage = 0;

});

function go() {
    playRunner = setInterval(function () {
        // Visualizers
        $visualizers.each(function () {
            $(this).css('height', Math.random() * 90 + 10 + '%');

        });

        // Progress bar
        // percentage += ($audioPlayer.currentTime / $audioPlayer.duration) * 100 * 0.15;
        // if (percentage > 100) percentage = 0; {
        //     clearInterval(playRunner); // Clear the interval when the song ends
        //     percentage = 0;
        // }

        // $progressBarRunner.css('width', percentage + '%');

        // Update the time dynamically
        $time.text(calculateTime($audioPlayer.duration, percentage));
    }, 250);
}

// Play button click event
$('.play-button').on('click', function () {
    if ($audioPlayer.paused) {
        $audioPlayer.play();
        $player.toggleClass('paused').toggleClass('playing');
        go();
    } else {
        $player.toggleClass('playing').toggleClass('paused');
        clearInterval(playRunner);
        $audioPlayer.pause();
    }
});

// Function to get the base64-encoded audio data for a specific song ID
function getAudioData(songId) {
    // Replace this URL with the endpoint of your Flask route
    var apiUrl = `/getsong/${songId}`;

    // Fetch the data from the Flask route
    return fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error('Song not found');
            }
            return response.json(); // Parse the response as JSON
        })
        .then(songData => {
            if (songData.error) {
                throw new Error(songData.error);
            }

            return {
                audioData: `data:audio/mp3;base64,${songData.audio_data}`,
                image: `data:image/jpeg;base64,${songData.image}`,
                songName: songData.song_name,
                singer: songData.singer,
                rating: songData.rating,
                lyrics: songData.lyrics
            };
        })
        .catch(error => {
            console.error(error);
            return null;
        });
}







// Function to get the audio data for a specific song ID
function updateAudioSource(songId) {
    // Get the source element by its ID
    var sourceElement = document.getElementById("song-audio");
    var imageElement = document.getElementById("song-image");
    var songNameElement = document.getElementById("song-name");
    var singerElement = document.getElementById("singer-name");
    var lyricsElement = document.getElementById("lyrics");
    var songIdElement = document.getElementById("song-id");
    var rateElement = document.getElementById("rate");


    // Check if the source element exists
    if (sourceElement) {
        // Get the new audio data for the specified song ID
        getAudioData(songId).then(newAudioData => {
            if (newAudioData) {
                sourceElement.src = newAudioData.audioData;
                imageElement.src = newAudioData.image;
                songNameElement.textContent = newAudioData.songName;
                singerElement.textContent = newAudioData.singer;
                songIdElement.textContent = songId;
                rateElement.textContent = newAudioData.rating;
                var lyricsLines = newAudioData.lyrics.split('\n');

                // Set the new content for the lyrics element
                lyricsElement.innerHTML = ''; // Clear existing content
                lyricsLines.forEach(line => {
                    // Create a new paragraph element for each line
                    var paragraph = document.createElement("p");
                    paragraph.textContent = line;
                    lyricsElement.appendChild(paragraph);
                });

                $audioPlayer.load();

            }
        });
    }
}

// Function to make a POST request to the recentlyplayed route // 
function addToRecentlyPlayed(newAudioId) {
    $.ajax({
        url: `/recentlyplayed/${newAudioId}`,
        type: 'POST',
        success: function (response) {
            console.log(response); // Log the response from the server
        },
        error: function (error) {
            console.error('Error:', error);
        }
    });
}


// event listener for play button
$('.play-btn').on('click', function () {
    footer.style.display = 'block';
    $player.addClass('paused').removeClass('playing');
    var $clickedPlayBtn = $(this);
    var newAudioId = $clickedPlayBtn.data('audio'); // Get the song ID from the data-audio attribute

    // Update the audio source and handle metadata
    updateAudioSource(newAudioId);

    // Wait for the audio to load
    $audioPlayer.addEventListener('loadedmetadata', function () {
        console.log('Loaded metadata');
        handleMetadata();
        // Play the audio
        $audioPlayer.play();
        console.log('Playing audio');
        $player.addClass('playing').removeClass('paused');
        go();
        // Make a POST request to the recentlyplayed route
        addToRecentlyPlayed(newAudioId);


    });
});





// Progress bar click event
$('.progress-bar').on('click', function (e) {
    var posX = $(this).offset().left;
    var clickX = e.pageX - posX;
    var width = $(this).width();
    percentage = (clickX / width) * 100;
    $audioPlayer.currentTime = (songLength * percentage) / 100;
});

function calculateTime(songLength, percentage) {
    // Time calculation
    var currentLength = (songLength / 100) * percentage;
    var minutes = Math.floor(currentLength / 60);
    var seconds = Math.floor(currentLength - minutes * 60);
    if (seconds <= 9) {
        return minutes + ':0' + seconds;
    } else {
        return minutes + ':' + seconds;
    }
}

// Clear interval initially
clearInterval(playRunner);


// Check if the closeButton element exists
if (songCloseButton) {
    // Add a click event listener
    songCloseButton.addEventListener('click', function () {

        // Check if the footer element exists
        if (footer) {
            clearInterval(playRunner);
            $player.addClass('paused').removeClass('playing');
            $audioPlayer.pause();
            footer.style.display = 'none';
        }
    });
}


// popup window ========================================================================================================

// Get references to the popup and close button
var popup = document.querySelector('.popup');
var downArrow = document.querySelector('.down-ar');

var closeButton = document.querySelector('.popup-close');

// Function to close the popup
function closePopup() {
    popup.style.display = 'none';
}
// Function to toggle the visibility of the popup
function togglePopup() {
    if (popup.style.display === 'none' || popup.style.display === '') {
        popup.style.display = 'flex';
    } else {
        popup.style.display = 'none';
    }
}

// Attach event listener to the down arrow
downArrow.addEventListener('click', togglePopup);
// Attach event listeners
closeButton.addEventListener('click', closePopup); 