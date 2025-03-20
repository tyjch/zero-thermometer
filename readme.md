# Steps

## Configure WiFi

### Raspberry Pi OS *Bookworm* (and later)
In Raspberry Pi OS *Bookworm*, `NetworkManager` is used to configure internet connections. 

### Raspberry Pi OS (earlier)
In older versions, you can edit `wpa_supplicant.conf` to set up WiFi connections instead.

## Install Git
```shell
sudo apt-get update
sudo apt-get install git
```
#### Optional: Configure Git
```shell
git config --global user.name "tyjch"
git config --global user.email "tyjchurchill@gmail.com"
```

## Clone Repository
```shell
git clone https://github.com/tyjch/zero-thermometer.git
```


## Set Environment Variables in `.env`


## Install Github Actions Runner

