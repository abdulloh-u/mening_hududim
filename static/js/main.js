// MENING HUDUDIM - Main Interactive Helper Scripts

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // 2. Dynamic District Loading by Region Selection
    const regionSelect = document.getElementById('id_region');
    const districtSelect = document.getElementById('id_district');

    if (regionSelect && districtSelect) {
        regionSelect.addEventListener('change', function () {
            const regionId = this.value;
            if (!regionId) {
                districtSelect.innerHTML = '<option value="">Avval viloyatni tanlang</option>';
                return;
            }

            districtSelect.innerHTML = '<option value="">Yuklanmoqda...</option>';

            fetch(`/locations/api/districts/${regionId}/`)
                .then(response => response.json())
                .then(data => {
                    districtSelect.innerHTML = '<option value="">Tuman / shaharni tanlang</option>';
                    data.districts.forEach(dist => {
                        const opt = document.createElement('option');
                        opt.value = dist.id;
                        opt.textContent = dist.name;
                        districtSelect.appendChild(opt);
                    });
                })
                .catch(err => {
                    console.error('Tumanlarni yuklashda xatolik:', err);
                    districtSelect.innerHTML = '<option value="">Xatolik yuz berdi</option>';
                });
        });
    }

    // 3. Image Upload Live Preview
    const imageInput = document.getElementById('id_image');
    const imagePreview = document.getElementById('preview_img_element');
    if (imageInput && imagePreview) {
        imageInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    imagePreview.src = e.target.result;
                    imagePreview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                imagePreview.style.display = 'none';
            }
        });
    }

    // 4. Copy Tracking Code Helper (textContent avoids HTML injection)
    window.copyTrackingCode = function (text) {
        if (!navigator.clipboard) {
            alert("Brauzeringiz nusxalashni qo'llab-quvvatlamaydi.");
            return;
        }
        navigator.clipboard.writeText(text).then(function () {
            const toast = document.createElement('div');
            toast.className = 'position-fixed bottom-0 end-0 p-3';
            toast.style.zIndex = '9999';

            const card = document.createElement('div');
            card.className = 'toast show align-items-center text-white bg-success border-0 shadow';
            card.setAttribute('role', 'alert');

            const row = document.createElement('div');
            row.className = 'd-flex';

            const body = document.createElement('div');
            body.className = 'toast-body';

            const icon = document.createElement('i');
            icon.className = 'fa-solid fa-check-circle me-2';
            const value = document.createElement('strong');
            value.textContent = text;

            body.appendChild(icon);
            body.appendChild(document.createTextNode(' Murojaat raqami nusxalandi: '));
            body.appendChild(value);
            row.appendChild(body);
            card.appendChild(row);
            toast.appendChild(card);
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        }).catch(function () {
            alert("Nusxalab bo'lmadi. Raqamni qo'lda nusxalang: " + text);
        });
    };
});
