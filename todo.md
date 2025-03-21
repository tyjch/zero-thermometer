# To Do
- ~~Get rid of averaging, just put everything in separately~~
- ~~Add wifi symbol w/ strength & network name on display screen~~
- ~~Display local IP address~~
- Optimize code to start up faster
- ~~Be able to access via SSH remotely~~
- ~~Be able to view logs remotely~~
- ~~Fix colors getting inverted~~
- Add high/low over specified period?
- Add line chart of temperature?
- Sync time over internet
- Script changes to /boot/firmware/config.txt don't seem correct
- Add modprobe w1-gpio and modprobe w1-therm on boot with `echo -e "w1-gpio\nw1-therm" | sudo tee -a /etc/modules`
- Make start up and shutdown layers for screen
- Add shutdown button
- Setup Raspberry Pi Connect
- Check measurement_buffer.db
- Use buttons to mark connected/disconnected ground state
- Button to turn off Pi gracefully
- Buttons to adjust bias
- Poll DS18B20 sensor frequently but only send updates to Influx every so often
- Implement flashing screen

## 3D Printing
- New case with SI7021 sensor exposed
- Add fan to case?
- Add buttons to case
- Add stand
- Add case with access to buttons