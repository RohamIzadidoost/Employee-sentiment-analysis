
// Handle Start Detection button
async function startStream() {
    try {
        const response = await fetch('/start', { method: 'POST' });
        const data = await response.json();
        console.log(data.status);
        document.getElementById('startButton').disabled = true;
        document.getElementById('stopButton').disabled = false;
        document.getElementById('videoFeed').style.display = 'block';
        updateEmotions();
    } catch (error) {
        console.error('Error starting stream:', error);
    }
}

// Handle Stop Detection button
async function stopStream() {
    try {
        const response = await fetch('/stop', { method: 'POST' });
        const data = await response.json();
        console.log(data.status);
        document.getElementById('startButton').disabled = false;
        document.getElementById('stopButton').disabled = true;
        document.getElementById('videoFeed').style.display = 'none';
    } catch (error) {
        console.error('Error stopping stream:', error);
    }
}

// Periodically update the detected emotions list
async function updateEmotions() {
    try {
        const response = await fetch('/emotions');
        const data = await response.json();
        const emotionList = document.getElementById('emotionList');
        emotionList.innerHTML = '';
        if (data.emotions.length > 0) {
            data.emotions.forEach(emotion => {
                const li = document.createElement('li');
                li.textContent = emotion;
                emotionList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'No emotions detected';
            emotionList.appendChild(li);
        }
    } catch (error) {
        console.error('Error fetching emotions:', error);
    }
    if (!document.getElementById('stopButton').disabled) {
        setTimeout(updateEmotions, 1000); // Update every 1 second
    }
}
