let updateTimeout;

async function fetchWeatherData(location, numDays, startDate = null, endDate = null) {
    try {
        // Clear previous data immediately
        const weatherContainer = document.getElementById('weather-container');
        weatherContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading weather data...</span></div></div>';

        let url = `/api/weather?location=${encodeURIComponent(location)}`;
        
        if (startDate && endDate) {
            url += `&start_date=${startDate}&end_date=${endDate}`;
        } else if (numDays) {
            url += `&num_days=${numDays}`;
        }
        
        console.log('Fetching weather data from:', url);
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.error) {
            console.error('Weather API error:', data.error);
            showError(data.error);
            return;
        }

        // Filter data if date range is specified
        let filteredData = data;
        if (startDate && endDate) {
            const start = new Date(startDate);
            const end = new Date(endDate);
            filteredData = data.filter(day => {
                const date = new Date(day.date);
                return date >= start && date <= end;
            });
        }

        console.log('Weather data received:', filteredData);
        if (filteredData.length === 0) {
            showError('No weather data available for the selected date range');
            return;
        }

        updateWeatherDisplay(filteredData);
    } catch (error) {
        console.error('Error fetching weather data:', error);
        showError('Unable to load weather data at this time.');
    }
}

function showError(message) {
    const weatherContainer = document.getElementById('weather-container');
    weatherContainer.innerHTML = `<div class="alert alert-warning">${message}</div>`;
}

function isValidDateRange(start, end) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Check if dates are valid
    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        return { valid: false, message: 'Invalid date format' };
    }
    
    // Check if end date is before start date
    if (end < start) {
        return { valid: false, message: 'End date must be after start date' };
    }
    
    // Check if start date is not more than 14 days in the past
    const minDate = new Date(today);
    minDate.setDate(minDate.getDate() - 14);
    if (start < minDate) {
        return { valid: false, message: 'Start date cannot be more than 14 days in the past' };
    }
    
    // Check if end date is not more than 14 days in the future
    const maxDate = new Date(today);
    maxDate.setDate(maxDate.getDate() + 14);
    if (end > maxDate) {
        return { valid: false, message: 'End date cannot be more than 14 days in the future' };
    }
    
    // Check if date range is not more than 14 days
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    if (diffDays > 14) {
        return { valid: false, message: 'Date range cannot exceed 14 days' };
    }
    
    return { valid: true };
}

function updateWeatherRange() {
    clearTimeout(updateTimeout);
    updateTimeout = setTimeout(() => {
        const startDate = document.getElementById('weatherStartDate').value;
        const endDate = document.getElementById('weatherEndDate').value;
        const destination = document.querySelector('h2').textContent.trim().split('\n')[0];
        
        console.log('Date range selected:', { startDate, endDate });
        
        if (!startDate || !endDate || !destination) {
            showError('Please ensure all fields are filled correctly');
            return;
        }
        
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        const validation = isValidDateRange(start, end);
        if (!validation.valid) {
            showError(validation.message);
            return;
        }
        
        console.log('Updating weather for destination:', destination);
        fetchWeatherData(destination, null, startDate, endDate);
    }, 300);
}

function convertToCelsius(fahrenheit) {
    return Math.round((fahrenheit - 32) * 5 / 9);
}

function updateWeatherDisplay(weatherData) {
    const weatherContainer = document.getElementById('weather-container');
    weatherContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading weather data...</span></div></div>';
    
    setTimeout(() => {
        weatherContainer.innerHTML = '';
        
        // Create alerts container
        const alertsContainer = document.createElement('div');
        alertsContainer.className = 'weather-alerts mb-3';
        
        // Process each day's data for alerts
        weatherData.forEach(day => {
            const alerts = detectWeatherAlerts({
                ...day,
                temperature: convertToCelsius(day.temperature)
            });
            if (alerts.length > 0) {
                const dayAlerts = document.createElement('div');
                dayAlerts.innerHTML = `
                    <h6 class="mb-2">${formatDate(day.date)} Alerts:</h6>
                    ${alerts.map(alert => `
                        <div class="weather-alert ${alert.severity.toLowerCase()}">
                            <i class="${getAlertIcon(alert.severity)}"></i>
                            <div>
                                <strong>${alert.event}</strong>
                                <div class="small">${alert.description}</div>
                            </div>
                        </div>
                    `).join('')}
                `;
                alertsContainer.appendChild(dayAlerts);
            }
        });
        
        // Add alerts to container if any exist
        if (alertsContainer.children.length > 0) {
            weatherContainer.appendChild(alertsContainer);
        }

        // Display daily forecasts
        weatherData.forEach((day, index) => {
            const dayElement = document.createElement('div');
            dayElement.className = 'weather-day mb-3 p-2 border-bottom';
            
            // Get weather icon based on condition
            const weatherIcon = getWeatherIcon(day.condition);
            
            // Create daily summary with Celsius temperature
            const dailySummary = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">${formatDate(day.date)}</h6>
                        <div class="weather-details">
                            <span class="condition">
                                <i class="${weatherIcon}"></i> 
                                ${day.condition}
                            </span>
                        </div>
                    </div>
                    <div class="text-end">
                        <span class="temp display-6">${convertToCelsius(day.temperature)}°C</span>
                        <div class="precipitation small">
                            <i class="fas fa-tint"></i> ${day.precipitation}%
                        </div>
                    </div>
                </div>
            `;

            // Create canvas for temperature trend graph
            const graphContainer = document.createElement('div');
            graphContainer.className = 'temperature-graph mt-3';
            const tempCanvas = document.createElement('canvas');
            tempCanvas.id = `temp-graph-${index}`;
            graphContainer.appendChild(tempCanvas);

            // Create canvas for precipitation probability graph
            const precipContainer = document.createElement('div');
            precipContainer.className = 'precipitation-graph mt-3';
            const precipCanvas = document.createElement('canvas');
            precipCanvas.id = `precip-graph-${index}`;
            precipContainer.appendChild(precipCanvas);

            // Create hourly forecast section with Celsius temperatures
            const hourlyForecast = `
                <div class="hourly-forecast mt-2">
                    <div class="hourly-scroll">
                        ${day.hourly.map(hour => `
                            <div class="hour-item">
                                <div class="hour-time">${formatHour(hour.time)}</div>
                                <div class="hour-icon">
                                    <i class="${getWeatherIcon(hour.condition)}"></i>
                                </div>
                                <div class="hour-temp">${convertToCelsius(hour.temperature)}°C</div>
                                <div class="hour-precip">
                                    <i class="fas fa-tint"></i> ${hour.precipitation}%
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;

            dayElement.innerHTML = dailySummary;
            dayElement.appendChild(graphContainer);
            dayElement.appendChild(precipContainer);
            dayElement.insertAdjacentHTML('beforeend', hourlyForecast);
            weatherContainer.appendChild(dayElement);

            // Create temperature trend graph with Celsius values
            createTemperatureGraph(day.hourly.map(hour => ({
                ...hour,
                temperature: convertToCelsius(hour.temperature)
            })), tempCanvas.id);
            // Create precipitation probability graph
            createPrecipitationGraph(day.hourly, precipCanvas.id);
        });
    }, 100);
}

function detectWeatherAlerts(weatherData) {
    const alerts = [];
    
    // Check temperature extremes (converted to Celsius thresholds)
    if (weatherData.temperature > 35) {  // 95°F ≈ 35°C
        alerts.push({
            severity: 'Severe',
            event: 'Extreme Heat',
            description: 'Temperature exceeds 35°C. Stay hydrated and avoid prolonged sun exposure.'
        });
    } else if (weatherData.temperature < 0) {  // 32°F = 0°C
        alerts.push({
            severity: 'Severe',
            event: 'Freezing Temperature',
            description: 'Temperature below 0°C. Take precautions against freezing conditions.'
        });
    }
    
    // Check precipitation probability
    if (weatherData.precipitation > 70) {
        alerts.push({
            severity: 'Severe',
            event: 'Heavy Precipitation',
            description: `High (${weatherData.precipitation}%) chance of precipitation. Prepare for wet conditions.`
        });
    } else if (weatherData.precipitation > 40) {
        alerts.push({
            severity: 'Moderate',
            event: 'Moderate Precipitation',
            description: `Moderate (${weatherData.precipitation}%) chance of precipitation. Consider rain gear.`
        });
    } else if (weatherData.precipitation > 20) {
        alerts.push({
            severity: 'Mild',
            event: 'Light Precipitation',
            description: `Light (${weatherData.precipitation}%) chance of precipitation.`
        });
    }
    
    // Check severe weather conditions
    if (weatherData.condition) {
        const condition = weatherData.condition.toLowerCase();
        if (condition.includes('thunderstorm')) {
            alerts.push({
                severity: 'Severe',
                event: 'Thunderstorm',
                description: 'Thunderstorm conditions expected. Stay indoors when possible.'
            });
        } else if (condition.includes('heavy rain')) {
            alerts.push({
                severity: 'Severe',
                event: 'Heavy Rain',
                description: 'Heavy rain expected. Be cautious of flooding.'
            });
        } else if (condition.includes('snow')) {
            alerts.push({
                severity: 'Moderate',
                event: 'Snow',
                description: 'Snowy conditions expected. Plan travel accordingly.'
            });
        }
    }
    
    return alerts;
}

function createTemperatureGraph(hourlyData, canvasId) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const temperatures = hourlyData.map(hour => hour.temperature);
    const times = hourlyData.map(hour => formatHour(hour.time));

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: times,
            datasets: [{
                label: 'Temperature (°C)',
                data: temperatures,
                borderColor: '#ff6b6b',
                backgroundColor: 'rgba(255, 107, 107, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y}°C`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '°C';
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function createPrecipitationGraph(hourlyData, canvasId) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const precipitations = hourlyData.map(hour => hour.precipitation);
    const times = hourlyData.map(hour => formatHour(hour.time));

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: times,
            datasets: [{
                label: 'Precipitation Probability',
                data: precipitations,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.y}% chance of precipitation`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function formatDate(dateString) {
    const options = { weekday: 'short', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

function formatHour(time) {
    const hour = parseInt(time.split(':')[0]);
    const meridiem = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}${meridiem}`;
}

function getWeatherIcon(condition) {
    const iconMap = {
        'Clear': 'fas fa-sun',
        'Clouds': 'fas fa-cloud',
        'Rain': 'fas fa-cloud-rain',
        'Snow': 'fas fa-snowflake',
        'Thunderstorm': 'fas fa-bolt',
        'Drizzle': 'fas fa-cloud-rain',
        'Mist': 'fas fa-smog',
        'Smoke': 'fas fa-smog',
        'Haze': 'fas fa-smog',
        'Dust': 'fas fa-smog',
        'Fog': 'fas fa-smog',
        'Sand': 'fas fa-smog',
        'Ash': 'fas fa-smog',
        'Squall': 'fas fa-wind',
        'Tornado': 'fas fa-wind'
    };
    
    return iconMap[condition] || 'fas fa-cloud';
}

function getAlertIcon(severity) {
    const iconMap = {
        'Severe': 'fas fa-exclamation-triangle',
        'Moderate': 'fas fa-exclamation-circle',
        'Mild': 'fas fa-info-circle'
    };
    return iconMap[severity] || 'fas fa-exclamation-circle';
}