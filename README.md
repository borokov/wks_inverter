# Reverse ingeneering protocole #

Hightly inspired by http://allican.be/blog/2017/01/28/reverse-engineering-cypress-serial-usb.html

## Capturing trace ##

Using USBPcap: https://desowin.org/usbpcap/tour.html
Generate an xxx.pcap that can be open with wireshark: https://www.wireshark.org/

watchpower_trace.pcap has been generating before starting watchpower. One can see initialisation at the begining of trace follow by streamed data.
