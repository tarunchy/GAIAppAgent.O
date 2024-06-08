$(document).ready(function () {
    function fetchData() {
        $.getJSON('/realtime', function (data) {
            var content = `
                <div class="mb-2 p-4 border rounded shadow">
                    <p><strong>Timestamp:</strong> ${data.Timestamp}</p>
                    <p><strong>Consumption (kWh):</strong> ${data.Consumption_kWh}</p>
                    <p><strong>Voltage (V):</strong> ${data.Voltage_V}</p>
                    <p><strong>Frequency (Hz):</strong> ${data.Frequency_Hz}</p>
                    <p><strong>Power Factor:</strong> ${data.PowerFactor}</p>
                    <p><strong>Reactive Power (kVAR):</strong> ${data.ReactivePower_kVAR}</p>
                    <p><strong>Current (A):</strong> ${data.Current_A}</p>
                    <p><strong>Transformer Temperature (°C):</strong> ${data.TransformerTemperature_C}</p>
                </div>`;
            $('#gridData').html(content);
            gsap.from("#gridData div", { duration: 1, opacity: 0, y: 50 });
        });
    }

    setInterval(fetchData, 3000);
    fetchData();
});
