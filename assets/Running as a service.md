# Running as a service

The audio capturee controller runs as a service, so that, at startup or any other instance, the code restarts or keeps running.

I used the followgin steps from chat and it worked nicely:

```bash
sudo nano /etc/systemd/system/my_script.service

```

make a file and paste this with proper inputs in there:

```bash
[Unit]
Description=Run Python script in venv at startup
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/myproject
ExecStart=/home/pi/myproject/venv/bin/python /home/pi/myproject/myscript.py
Restart=on-failure

[Install]
WantedBy=multi-user.target

```

then save and exit and run the following sequence of commands:

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable my_script.service
sudo systemctl start my_script.service

```

works just ifne, and to check for updates/status, run:

```bash
systemctl status my_script.service
```

also commands exist:

`disable`

`restart`

`stop`

`is-enabled`