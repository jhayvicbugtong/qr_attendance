
import qrcode

data = "Hello, Mac!"
qr = qrcode.make(data)
qr.show()  # Should display the QR code
qr.save("test_qr.png")  # Should save the QR code
