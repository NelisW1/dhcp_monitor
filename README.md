# dhcp_monitor
Monitors the LAN for DHCP requests: 

- sends push notification to your phone through PushBullet.
- stores data about the requests into a SQLite database.
- receive weekly and or monthly reports by email: html email with a pdf attached.

How to use:
1. Paste the complete folder to your system.
2. Create an account at Pushbullet and download the Pushbullet app on your phone.
3. Put the API Token into the dhcp_monitor_2.py script at 'pb_token'.
4. use Cron or another tool to schedule the reporting.py weekly or monthly.
  - Weekly: shows the previous week. Schedule to execute on the 1st day of the week.
  - Monthly: shows the previous month. Schedule to execute on the 1st of every month.
5. extra requirement for pdf module:
   Make sure to have wkhtmltopdf installed:
   https://wkhtmltopdf.org/downloads.html
