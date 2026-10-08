"""Generate six reproducible 600 dpi QR images for the course exit form."""
from pathlib import Path
import qrcode
import skh_palette as skh
skh.use()
root=Path(__file__).resolve().parents[1]
origin='https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site'
for session in range(1,7):
 qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=22,border=4)
 qr.add_data(f'{origin}/?session={session}');qr.make(fit=True)
 qr.make_image(fill_color=skh.C['graphite'],back_color='white').save(root/'assets'/f'exit-qr-{session:02d}.png',dpi=(600,600))
