$(document).ready(function () {
    var ctx = document.getElementById('gridChart').getContext('2d');
    var chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Consumption (kWh)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                data: [],
                fill: false
            }]
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Real-time Grid Data'
            },
            scales: {
                x: {
                    type: 'realtime',
                    realtime: {
                        duration: 20000,
                        refresh: 3000,
                        delay: 2000,
                        onRefresh: fetchData
                    }
                },
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    function fetchData() {
        $.getJSON('/realtime', function (data) {
            chart.data.labels.push(data.Timestamp);
            chart.data.datasets[0].data.push(data.Consumption_kWh);
            chart.update();
            gsap.from("#gridChart", { duration: 1, opacity: 0, y: 50 });
        });
    }
    
    fetchData();
    setInterval(fetchData, 3000);
});
