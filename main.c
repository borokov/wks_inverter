#include <stdio.h>
#include <string.h>
#include <assert.h>

#include <libusb-1.0/libusb.h>

#define TRUE 1
#define FALSE 0
#define bool uint8_t


unsigned short 
crc16(char *ptr, int count)
{
   int  crc;
   char i;
   crc = 0;
   while (--count >= 0)
   {
      crc = crc ^ (int) *ptr++ << 8;
      i = 8;
      do
      {
         if (crc & 0x8000)
            crc = crc << 1 ^ 0x1021;
         else
            crc = crc << 1;
      } while(--i);
   }
   return (crc);
}

void
formatCommand(char cmd[8])
{
   size_t len = strlen(cmd);
   memset(cmd + len, '\0', 8 - len);
   unsigned short crc = crc16(cmd, len);
   // Reverse endianess
   unsigned short crc_BE = ((crc & 0xff00) >> 8) | ((crc & 0x00ff) << 8);
   *((unsigned short*)(cmd + len)) = crc_BE;
   cmd[len+2] = '\r';
}

void sendCommand(libusb_device_handle* dev_handle, char cmd[8])
{
   formatCommand(cmd);

   // rc = libusb_bulk_transfer(dev_handle, (64 | LIBUSB_ENDPOINT_OUT), data, 8, &actual, 0);
   // bmRequestType=0x21 # REQUEST_TYPE_CLASS | RECIPIENT_INTERFACE | ENDPOINT_OUT
   // bRequest=0x9 # SET_REPORT
   // wValue=0x200
   // wIndex=0
   int rc = libusb_control_transfer(dev_handle, 0x21, 0x9, 0x200, 0, cmd, 8, 0);
   assert (rc == 8);
}

void print_error(int error_code)
{
   if ( error_code == LIBUSB_ERROR_TIMEOUT )
   {
      printf("LIBUSB_ERROR_TIMEOUT\n");
   }
   else if ( error_code == LIBUSB_ERROR_PIPE )
   {
      printf("LIBUSB_ERROR_PIPE\n");
   }
   else if ( error_code == LIBUSB_ERROR_NO_DEVICE )
   {
      printf("LIBUSB_ERROR_NO_DEVICE\n");
   }
   else if ( error_code == LIBUSB_ERROR_BUSY )
   {
      printf("LIBUSB_ERROR_BUSY\n");
   }
   else if ( error_code == LIBUSB_ERROR_INVALID_PARAM )
   {
      printf("LIBUSB_ERROR_INVALID_PARAM\n");
   }
   else if ( error_code < 0 )
   {
      printf("UNKNOWN ERROR: %d\n", error_code);
   }
}

void get_frame(libusb_device_handle* dev_handle)
{
   char data[1024];
   memset(data, 0, sizeof(data));
   
   bool ok = TRUE;
   char* data_ptr = data;

   //-------------------------------------------------
   // Read 8 bytes by 8 bytes until we found '\r'
   // Note: device zeros bad to always send 8 bytes
   char* end_of_frame = NULL;
   do
   {
      int actual_len = 0;
      int rc = libusb_bulk_transfer(dev_handle, 0x81, data_ptr, 8, &actual_len, 1000);
      if ( rc != 0 )
      {
         print_error(rc);
         if ( rc != LIBUSB_ERROR_TIMEOUT )
            assert(FALSE);
      }
      data_ptr += actual_len;
      // real frame ends with '\r' but device zeros pad to send 8 byte each time so frame len
      // is not sum of all read bytes
      end_of_frame = strstr(data, "\r");
   } while( end_of_frame == NULL );


   //----------------------------------------------------
   // Now check if frame is valid

   // Remove last '\r'
   size_t buffer_len = end_of_frame - data;

   // We should have at least 1 byte of data and 2 bytes of CRC. Else, something goen wrong. 
   if ( buffer_len >= 3 )
   {
      uint16_t computed_crc = crc16(data, buffer_len - 2);

      char* crc_ptr = data + buffer_len - 2;
      uint16_t frame_crc = (crc_ptr[0] << 8) | crc_ptr[1];

      if ( computed_crc != frame_crc )
      {
         printf("bad CRC\n");
         ok = FALSE;
      }
   }
   else
   {
      ok = FALSE;
   }

   if ( ok )
      printf("data: %s\n", data);
}

int main()
{
   libusb_context* context    = NULL;
   libusb_device_handle* dev_handle = NULL;
   libusb_device** devs;
   int rc = 0;
   ssize_t count; //holding number of devices in list

   unsigned short VENDOR_ID = 0x0665;
   unsigned short PRODUCT_ID = 0x5161;

   rc = libusb_init(&context);
   assert(rc == 0);

   dev_handle = libusb_open_device_with_vid_pid(context,VENDOR_ID,PRODUCT_ID);
   assert(dev_handle != NULL);

   if(libusb_kernel_driver_active(dev_handle, 0))
   {
      rc = libusb_detach_kernel_driver(dev_handle, 0); // detach driver
      assert(rc == 0);
   }

   rc = libusb_claim_interface(dev_handle, 0);
   assert(rc == 0);

   rc = libusb_set_interface_alt_setting(dev_handle, 0, 0);
   assert(rc == 0);

   //-----------------------------------------------------------
   // OK, everything is configured, lets send some commands

   char data[8] = "QPGS0";
   sendCommand(dev_handle, data);

   get_frame(dev_handle);

   //-----------------------------------------------------------
   // Release everything


   rc = libusb_release_interface(dev_handle, 0);
   assert(rc == 0);
   libusb_close(dev_handle);
   libusb_exit(context);

   return 0;

}