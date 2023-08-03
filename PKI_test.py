from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime


#https://qiita.com/keys/items/81316fad4ca5e055da9e
#https://qiita.com/bashaway/items/ac5ece9618a613f37ce5


class Certificate:
    def generate_private_key():
        # RSA秘密鍵を生成
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        return private_key


    def save_private_key_to_pem(private_key, filename):
        # 秘密鍵をPEM形式でファイルに保存
        with open(filename, "wb") as key_file:
            key_file.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))


    def generate_self_signed_certificate(private_key):
        # 秘密鍵から公開鍵を取得
        public_key = private_key.public_key()

        # 証明書のsubjectとissuerを設定
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"JP"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Osaka"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, u"Osaka"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"xxxxx"),
            x509.NameAttribute(NameOID.COMMON_NAME, u"xxxxx.com"),
        ])

        # 自己署名証明書を生成
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            # 証明書の有効期限を1年後に設定
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            # Subject Alternative Nameを追加
            x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
            critical=False,
        ).sign(private_key, hashes.SHA256())

        return cert


    def save_certificate_to_pem(cert, filename):
        # 証明書をPEM形式でファイルに保存
        with open(filename, "wb") as cert_file:
            cert_file.write(cert.public_bytes(serialization.Encoding.PEM))


def main():
    # 秘密鍵の生成と保存
    private_key = Certificate.generate_private_key()
    Certificate.save_private_key_to_pem(private_key, "private_key.pem")

    # 自己署名証明書の生成と保存
    cert = Certificate.generate_self_signed_certificate(private_key)
    Certificate.save_certificate_to_pem(cert, "certificate.pem")



#START
CertificateInstance = Certificate()
main()

#END