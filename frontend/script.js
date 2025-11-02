// Configuration - Automatically detect API URL from current page origin
// The API runs on the same server, so we use the same origin
const API_BASE_URL = window.location.origin;
const API_ENDPOINT = `${API_BASE_URL}/ask`;

// Initialize background animation (softer, medical theme)
function initBackgroundAnimation() {
    const container = document.getElementById('backgroundAnimation');
    
    // Create fewer, softer pulsing circles for medical theme
    for (let i = 0; i < 4; i++) {
        const circle = document.createElement('div');
        circle.style.position = 'absolute';
        circle.style.width = `${120 + i * 60}px`;
        circle.style.height = `${120 + i * 60}px`;
        circle.style.borderRadius = '50%';
        circle.style.background = `rgba(255, 255, 255, ${0.03 + i * 0.015})`;
        circle.style.filter = 'blur(50px)';
        
        // Random initial position
        const x = Math.random() * 100;
        const y = Math.random() * 100;
        circle.style.left = `${x}%`;
        circle.style.top = `${y}%`;
        
        container.appendChild(circle);
        
        // Animate with anime.js - slower, more gentle
        anime({
            targets: circle,
            translateX: [
                { value: anime.random(-150, 150), duration: anime.random(4000, 6000) },
                { value: anime.random(-150, 150), duration: anime.random(4000, 6000) }
            ],
            translateY: [
                { value: anime.random(-150, 150), duration: anime.random(4000, 6000) },
                { value: anime.random(-150, 150), duration: anime.random(4000, 6000) }
            ],
            scale: [
                { value: anime.random(0.9, 1.1), duration: anime.random(3000, 5000) },
                { value: anime.random(0.9, 1.1), duration: anime.random(3000, 5000) }
            ],
            opacity: [
                { value: anime.random(0.03, 0.08), duration: anime.random(3000, 5000) },
                { value: anime.random(0.03, 0.08), duration: anime.random(3000, 5000) }
            ],
            easing: 'easeInOutSine',
            loop: true,
            direction: 'alternate'
        });
    }
}

// Initialize heartbeat animation
function initHeartbeatAnimation() {
    const heartbeatCircle = document.getElementById('heartbeatCircle');
    
    if (!heartbeatCircle) return;
    
    // Create heartbeat pulsing effect using anime.js
    anime({
        targets: heartbeatCircle,
        scale: [
            { value: 1, duration: 500 },
            { value: 1.3, duration: 200, easing: 'easeOutQuad' },
            { value: 1, duration: 300, easing: 'easeInQuad' },
            { value: 1.15, duration: 200, easing: 'easeOutQuad' },
            { value: 1, duration: 400, easing: 'easeInQuad' },
        ],
        opacity: [
            { value: 0.3, duration: 500 },
            { value: 0.6, duration: 200 },
            { value: 0.3, duration: 300 },
            { value: 0.5, duration: 200 },
            { value: 0.3, duration: 400 },
        ],
        loop: true,
        easing: 'linear'
    });
}

// Submit query to API
async function submitQuery() {
    const queryInput = document.getElementById('medicalQuery');
    const query = queryInput.value.trim();
    
    if (!query) {
        alert('Please enter a medical question.');
        return;
    }
    
    // Show loading state
    const submitBtn = document.getElementById('submitBtn');
    const buttonText = submitBtn.querySelector('.button-text');
    const loader = document.getElementById('loader');
    
    buttonText.textContent = 'Processing...';
    loader.style.display = 'flex';
    submitBtn.disabled = true;
    
    // Fade out previous results smoothly
    const responseSection = document.getElementById('responseSection');
    const errorSection = document.getElementById('errorSection');
    
    if (responseSection.style.display === 'grid') {
        anime({
            targets: responseSection,
            opacity: [1, 0],
            duration: 300,
            easing: 'easeInQuad',
            complete: function() {
                responseSection.style.display = 'none';
                responseSection.classList.remove('visible');
            }
        });
    }
    
    if (errorSection.style.display === 'block') {
        anime({
            targets: errorSection,
            opacity: [1, 0],
            duration: 300,
            easing: 'easeInQuad',
            complete: function() {
                errorSection.style.display = 'none';
            }
        });
    }
    
    try {
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        console.error('Error:', error);
        displayError(`Failed to get response: ${error.message}. Make sure the server is running at ${API_BASE_URL}`);
    } finally {
        // Reset button state
        buttonText.textContent = 'Ask Question';
        loader.style.display = 'none';
        submitBtn.disabled = false;
    }
}

// Display results in cards with smooth fade transitions
function displayResults(data) {
    const responseSection = document.getElementById('responseSection');
    
    // Update content
    document.getElementById('diagnosisContent').textContent = data.diagnosis || 'No diagnosis provided.';
    document.getElementById('adviceContent').textContent = data.advice || 'No advice provided.';
    
    // Fade in response section
    responseSection.style.display = 'grid';
    
    // Smooth fade-in animation for the section
    anime({
        targets: responseSection,
        opacity: [0, 1],
        duration: 500,
        easing: 'easeOutQuad',
        begin: function() {
            responseSection.classList.add('visible');
        }
    });
    
    // Staggered card animations with fade-in
    const cards = document.querySelectorAll('.card');
    anime({
        targets: cards,
        opacity: [0, 1],
        translateY: [40, 0],
        delay: anime.stagger(150),
        duration: 700,
        easing: 'easeOutExpo',
        begin: function() {
            cards.forEach(card => card.classList.add('visible'));
        }
    });
    
    // Scroll to results smoothly
    setTimeout(() => {
        responseSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

// Display error message with fade-in
function displayError(message) {
    const errorSection = document.getElementById('errorSection');
    document.getElementById('errorMessage').textContent = message;
    
    // Hide response section if visible
    const responseSection = document.getElementById('responseSection');
    if (responseSection.style.display === 'grid') {
        anime({
            targets: responseSection,
            opacity: [1, 0],
            duration: 300,
            easing: 'easeInQuad',
            complete: function() {
                responseSection.style.display = 'none';
            }
        });
    }
    
    // Show and fade in error section
    errorSection.style.display = 'block';
    anime({
        targets: errorSection,
        opacity: [0, 1],
        duration: 400,
        easing: 'easeOutQuad'
    });
    
    // Animate error card
    anime({
        targets: '.error-card',
        opacity: [0, 1],
        scale: [0.9, 1],
        duration: 500,
        easing: 'easeOutExpo'
    });
    
    // Scroll to error
    setTimeout(() => {
        errorSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

// Allow Enter key to submit (Shift+Enter for new line)
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('medicalQuery');
    
    textarea.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            submitQuery();
        }
    });
    
    // Initialize animations
    initBackgroundAnimation();
    initHeartbeatAnimation();
    
    // Check API health on load
    checkAPIHealth();
});

// Check if API is available
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        if (response.ok) {
            console.log('✅ API is available');
        }
    } catch (error) {
        console.warn('⚠️ API health check failed:', error.message);
        console.info(`API endpoint: ${API_BASE_URL}`);
    }
}

