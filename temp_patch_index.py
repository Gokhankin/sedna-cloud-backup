with open('index.html', 'r', encoding='utf-8') as f:
    code = f.read()

old_eod = '''            // Calculate and set End of Day (EOD) Pax: In-house + Arrivals - Departures
            const eodPax = Math.max(0, inhousePax + arrivalsPax - departuresPax);
            document.getElementById('pax-eod').innerText = `${eodPax} Pax`;'''

new_eod = '''            // Calculate and set End of Day (EOD) Pax:
            // For future dates, inhousePax is already the exact forecast Pax.
            // For today, EOD Pax = currently checked-in Pax + pending arrivals Pax - pending departures Pax.
            let eodPax;
            if (appData.report_date && selectedDate && selectedDate > appData.report_date) {
                eodPax = inhousePax;
            } else {
                eodPax = Math.max(0, inhousePax + arrivalsPax - departuresPax);
            }
            document.getElementById('pax-eod').innerText = `${eodPax} Pax`;'''

if old_eod in code:
    code = code.replace(old_eod, new_eod)
    print("Successfully patched eodPax calculation in index.html!")
else:
    print("Target eodPax block not found in index.html!")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(code)

print("Saved updated index.html!")
