#include <stdio.h>
#include <string.h>
#include <assert.h>

#include <libusb-1.0/libusb.h>


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

char
is_in(char value, char* buff, size_t buff_len)
{
   for ( int i = 0; i < buff_len; i++ )
   {
      if ( buff[i] == value )
         return 255;
   }
   return 0;
}

void get_frame(libusb_device_handle* dev_handle)
{
   char data[1024];
   memset(data, 0, sizeof(data));
   
   char ok = 1;
   char* data_ptr = data;
   do
   {
      while ( !is_in('\r', data, sizeof(data)) )
      {
         int actual_len = 0;
         int rc = libusb_bulk_transfer(dev_handle, 0x81, data_ptr, 8, &actual_len, 1000); // <-- Touche plus ça marche !!!
         if ( rc != 0 )
         {
            print_error(rc);
            if ( rc != LIBUSB_ERROR_TIMEOUT )
               assert(0);
         }
         data_ptr += actual_len;
      }

      size_t buffer_len = data_ptr - data;
      if ( buffer_len < 3 )
         ok = 0;

      uint16_t computed_crc = crc16(data, buffer_len - 2);
      uint16_t frame_crc = *((uint16_t*) (data + buffer_len - 2));

      if ( computed_crc != frame_crc )
         ok = 0;

   } while ( !ok );

   printf("data: %s\n", data);

   //assert (rc == 0);
/*
   values = ""
   bool ok = false
   while (!ok)
   {
      bool error = false
      char res[1024];
      int i = 0
      while ( '\r' not in res and i<20 )
      {
         try
         {
            res += "".join([chr(i) for i in dev.read(0x81, 8, timeout) if i!=0x00])
         }
         catch( usb.core.USBError as e: )
         {
            if e.errno == 110: // timeout. This happen quite often
               pass
            else:
               print(traceback.format_exc())
            throw;
         }
         i++;

         if len(res) < 3
         {
            error = True
            break;
         }

         crc = res[len(res)-3:-1]
         values = res[:-3]

         frame_crc_int = int.from_bytes([ord(crc[0]), ord(crc[1])], 'big')
         computed_crc_int = crc16.crc16xmodem(values.encode('utf-8'))

         if frame_crc_int != computed_crc_int
            error = True

         if len(values) < 2
            error = True

         if not error
            ok = True
      }  
   }
   print("Out get_frame")
   return values*/
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