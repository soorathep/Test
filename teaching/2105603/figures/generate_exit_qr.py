"""Generate 600 dpi QR images for the course exit forms."""
import argparse
from pathlib import Path

import qrcode
import skh_palette as skh


def main():
    sessions = range(1, 8)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=int, choices=sessions)
    args = parser.parse_args()
    skh.use()
    assets = Path(__file__).resolve().parents[1] / "assets"
    origin = "https://thermo-2105603-exit-ticket.soorathep-k.chatgpt.site"
    for session in [args.session] if args.session else sessions:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=22, border=4)
        qr.add_data(f"{origin}/?session={session}")
        qr.make(fit=True)
        image = qr.make_image(fill_color=skh.C["graphite"], back_color="white")
        image.save(assets / f"exit-qr-{session:02d}.png", dpi=(600, 600))


if __name__ == "__main__":
    main()
