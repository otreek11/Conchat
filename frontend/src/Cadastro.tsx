import { useState } from 'react';
import './Cadastro.css';

const BASE_URL = "http://localhost:8000/api/v1";

// ==================== INTERFACES E TIPOS ====================

interface FormData {
  username: string;
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  pfp: File | null;
}

interface FormErrors {
  username?: string;
  name?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  pfp?: string;
  general?: string;
}

interface ApiSuccessResponse {
  uuid: string;
  pfp_url: string | null;
  created_at: string;
  access_token: string;
  refresh_token: string;
  message: string;
}

interface ApiErrorResponse {
  message: string;
}

type PasswordStrength = 'weak' | 'medium' | 'strong';

// ==================== COMPONENTE PRINCIPAL ====================

function Cadastro() {
  // ==================== ESTADOS ====================

  const [formData, setFormData] = useState<FormData>({
    username: '',
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    pfp: null,
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Set<keyof FormData>>(new Set());
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>('weak');
  const [showSuccess, setShowSuccess] = useState<boolean>(false);

  // ==================== FUNÇÕES DE VALIDAÇÃO ====================

  const validateUsername = (username: string): string | undefined => {
    if (!username.trim()) {
      return 'Username é obrigatório';
    }
    if (username.length > 32) {
      return 'Username deve ter no máximo 32 caracteres';
    }
    const usernameRegex = /^[a-zA-Z0-9_-]+$/;
    if (!usernameRegex.test(username)) {
      return 'Username pode conter apenas letras, números, _ e -';
    }
    return undefined;
  };

  const validateName = (name: string): string | undefined => {
    if (!name.trim()) {
      return 'Nome é obrigatório';
    }
    if (name.length < 2) {
      return 'Nome deve ter pelo menos 2 caracteres';
    }
    if (name.length > 80) {
      return 'Nome deve ter no máximo 80 caracteres';
    }
    return undefined;
  };

  const validateEmail = (email: string): string | undefined => {
    if (!email.trim()) {
      return 'Email é obrigatório';
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return 'Email inválido';
    }
    if (email.length > 254) {
      return 'Email deve ter no máximo 254 caracteres';
    }
    return undefined;
  };

  const validatePassword = (password: string): string | undefined => {
    if (!password) {
      return 'Senha é obrigatória';
    }
    if (password.length < 8) {
      return 'Senha deve ter no mínimo 8 caracteres';
    }
    return undefined;
  };

  const validateConfirmPassword = (confirmPassword: string, password: string): string | undefined => {
    if (!confirmPassword) {
      return 'Confirmação de senha é obrigatória';
    }
    if (confirmPassword !== password) {
      return 'As senhas não coincidem';
    }
    return undefined;
  };

  const calculatePasswordStrength = (password: string): PasswordStrength => {
    if (password.length < 8) return 'weak';

    let strength = 0;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    if (strength <= 2) return 'weak';
    if (strength <= 3) return 'medium';
    return 'strong';
  };

  const validateField = (field: keyof FormData, value: any): boolean => {
    let error: string | undefined;

    switch (field) {
      case 'username':
        error = validateUsername(value);
        break;
      case 'name':
        error = validateName(value);
        break;
      case 'email':
        error = validateEmail(value);
        break;
      case 'password':
        error = validatePassword(value);
        break;
      case 'confirmPassword':
        error = validateConfirmPassword(value, formData.password);
        break;
    }

    setErrors((prev) => ({ ...prev, [field]: error }));
    return !error;
  };

  const validateAllFields = (): boolean => {
    const newErrors: FormErrors = {};

    newErrors.username = validateUsername(formData.username);
    newErrors.name = validateName(formData.name);
    newErrors.email = validateEmail(formData.email);
    newErrors.password = validatePassword(formData.password);
    newErrors.confirmPassword = validateConfirmPassword(formData.confirmPassword, formData.password);

    setErrors(newErrors);

    return !Object.values(newErrors).some((error) => error !== undefined);
  };

  // ==================== HANDLERS ====================

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Se o campo já foi tocado, valida em tempo real
    if (touched.has(name as keyof FormData)) {
      validateField(name as keyof FormData, value);
    }

    // Atualiza força da senha em tempo real
    if (name === 'password') {
      setPasswordStrength(calculatePasswordStrength(value));
    }

    // Se estiver editando confirmPassword, revalida caso password tenha mudado
    if (name === 'password' && touched.has('confirmPassword')) {
      validateField('confirmPassword', formData.confirmPassword);
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setTouched((prev) => new Set(prev).add(name as keyof FormData));
    validateField(name as keyof FormData, value);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;

    if (file) {
      // Validar tamanho (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setErrors((prev) => ({ ...prev, pfp: 'Imagem deve ter no máximo 5MB' }));
        return;
      }

      // Validar extensão
      const allowedExtensions = ['png', 'jpg', 'jpeg', 'webp'];
      const extension = file.name.split('.').pop()?.toLowerCase();
      if (!extension || !allowedExtensions.includes(extension)) {
        setErrors((prev) => ({ ...prev, pfp: 'Formato inválido. Use: png, jpg, jpeg ou webp' }));
        return;
      }

      // Criar preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);

      setFormData((prev) => ({ ...prev, pfp: file }));
      setErrors((prev) => ({ ...prev, pfp: undefined }));
    } else {
      setFormData((prev) => ({ ...prev, pfp: null }));
      setPreviewUrl(null);
    }
  };

  const handleRemoveImage = () => {
    setFormData((prev) => ({ ...prev, pfp: null }));
    setPreviewUrl(null);
    // Limpar input file
    const fileInput = document.getElementById('pfp') as HTMLInputElement;
    if (fileInput) fileInput.value = '';
  };

  // ==================== INTEGRAÇÃO BACKEND ====================

  const handleApiError = (status: number, data: ApiErrorResponse) => {
    switch (status) {
      case 400:
        setErrors((prev) => ({
          ...prev,
          general: data.message || 'Dados inválidos. Verifique os campos.',
        }));
        break;

      case 409:
        const message = data.message || '';
        if (message.includes('Username')) {
          setErrors((prev) => ({
            ...prev,
            username: 'Este username já está em uso',
          }));
        } else if (message.includes('Email')) {
          setErrors((prev) => ({
            ...prev,
            email: 'Este email já está cadastrado',
          }));
        } else {
          setErrors((prev) => ({
            ...prev,
            general: message,
          }));
        }
        break;

      case 500:
        setErrors((prev) => ({
          ...prev,
          general: 'Erro interno do servidor. Tente novamente mais tarde.',
        }));
        break;

      default:
        setErrors((prev) => ({
          ...prev,
          general: data.message || 'Erro desconhecido. Tente novamente.',
        }));
    }
  };

  const handleApiSuccess = (data: ApiSuccessResponse) => {
    // Salvar tokens no localStorage
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user_uuid', data.uuid);
    if (data.pfp_url) {
      localStorage.setItem('user_pfp', data.pfp_url);
    }

    // Mostrar mensagem de sucesso
    setShowSuccess(true);

    // Limpar formulário
    setFormData({
      username: '',
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
      pfp: null,
    });
    setPreviewUrl(null);
    setTouched(new Set());
    setErrors({});

    // Log para debug (roteamento será implementado futuramente)
    console.log('Usuário cadastrado com sucesso:', data.uuid);
    console.log('Tokens salvos no localStorage');
  };

  const submitForm = async () => {
    const formDataToSend = new FormData();
    formDataToSend.append('username', formData.username.trim());
    formDataToSend.append('name', formData.name.trim());
    formDataToSend.append('email', formData.email.trim());
    formDataToSend.append('password', formData.password);
    
    if (formData.pfp) {
      formDataToSend.append('pfp', formData.pfp);
    }

    try {
      const response = await fetch(BASE_URL + "/users", {
        method: 'POST',
        body: formDataToSend,
      });

      const data = await response.json();

      if (!response.ok) {
        handleApiError(response.status, data);
        return;
      }

      handleApiSuccess(data);
    } catch (error) {
      console.error('Erro na requisição:', error);
      setErrors((prev) => ({
        ...prev,
        general: 'Erro ao conectar com o servidor. Tente novamente.',
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Marcar todos os campos como tocados
    setTouched(
      new Set<keyof FormData>(['username', 'name', 'email', 'password', 'confirmPassword'])
    );

    // Validar todos os campos
    const isValid = validateAllFields();
    if (!isValid) return;

    setIsLoading(true);
    setErrors((prev) => ({ ...prev, general: undefined }));

    try {
      await submitForm();
    } finally {
      setIsLoading(false);
    }
  };

  // ==================== RENDER ====================

  return (
    <div className="cadastro-container">
      <div className="cadastro-card">
        <header className="cadastro-header">
          <h1>Criar Conta</h1>
          <p>Junte-se à comunidade Conchat</p>
        </header>

        {showSuccess && (
          <div className="success-message" role="alert">
            <p>Conta criada com sucesso! Bem-vindo ao Conchat.</p>
          </div>
        )}

        {errors.general && (
          <div className="error-message-general" role="alert">
            <p>{errors.general}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="cadastro-form" noValidate>
          {/* Username */}
          <div className="form-group">
            <label htmlFor="username" className="form-label">
              Username <span className="required">*</span>
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`form-input ${errors.username && touched.has('username') ? 'input-error' : ''}`}
              placeholder="seu_username"
              maxLength={32}
              aria-invalid={!!errors.username && touched.has('username')}
              aria-describedby={errors.username ? 'username-error' : undefined}
              disabled={isLoading}
            />
            {errors.username && touched.has('username') && (
              <span id="username-error" className="error-message" role="alert">
                {errors.username}
              </span>
            )}
          </div>

          {/* Nome */}
          <div className="form-group">
            <label htmlFor="name" className="form-label">
              Nome <span className="required">*</span>
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`form-input ${errors.name && touched.has('name') ? 'input-error' : ''}`}
              placeholder="Seu Nome"
              maxLength={80}
              aria-invalid={!!errors.name && touched.has('name')}
              aria-describedby={errors.name ? 'name-error' : undefined}
              disabled={isLoading}
            />
            {errors.name && touched.has('name') && (
              <span id="name-error" className="error-message" role="alert">
                {errors.name}
              </span>
            )}
          </div>

          {/* Email */}
          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Email <span className="required">*</span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`form-input ${errors.email && touched.has('email') ? 'input-error' : ''}`}
              placeholder="seu@email.com"
              maxLength={254}
              aria-invalid={!!errors.email && touched.has('email')}
              aria-describedby={errors.email ? 'email-error' : undefined}
              disabled={isLoading}
            />
            {errors.email && touched.has('email') && (
              <span id="email-error" className="error-message" role="alert">
                {errors.email}
              </span>
            )}
          </div>

          {/* Senha */}
          <div className="form-group">
            <label htmlFor="password" className="form-label">
              Senha <span className="required">*</span>
            </label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`form-input ${errors.password && touched.has('password') ? 'input-error' : ''}`}
              placeholder="••••••••"
              aria-invalid={!!errors.password && touched.has('password')}
              aria-describedby={errors.password ? 'password-error' : 'password-strength'}
              disabled={isLoading}
            />
            {formData.password && (
              <div
                id="password-strength"
                className={`password-strength strength-${passwordStrength}`}
              >
                <div className="strength-bar">
                  <div className="strength-fill"></div>
                </div>
                <span className="strength-text">
                  Força:{' '}
                  {passwordStrength === 'weak'
                    ? 'Fraca'
                    : passwordStrength === 'medium'
                    ? 'Média'
                    : 'Forte'}
                </span>
              </div>
            )}
            {errors.password && touched.has('password') && (
              <span id="password-error" className="error-message" role="alert">
                {errors.password}
              </span>
            )}
          </div>

          {/* Confirmar Senha */}
          <div className="form-group">
            <label htmlFor="confirmPassword" className="form-label">
              Confirmar Senha <span className="required">*</span>
            </label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              onBlur={handleBlur}
              className={`form-input ${
                errors.confirmPassword && touched.has('confirmPassword') ? 'input-error' : ''
              }`}
              placeholder="••••••••"
              aria-invalid={!!errors.confirmPassword && touched.has('confirmPassword')}
              aria-describedby={errors.confirmPassword ? 'confirm-password-error' : undefined}
              disabled={isLoading}
            />
            {errors.confirmPassword && touched.has('confirmPassword') && (
              <span id="confirm-password-error" className="error-message" role="alert">
                {errors.confirmPassword}
              </span>
            )}
          </div>

          {/* Imagem de Perfil */}
          <div className="form-group">
            <label htmlFor="pfp" className="form-label">
              Foto de Perfil <span className="optional">(opcional)</span>
            </label>
            <div className="file-upload-container">
              <input
                type="file"
                id="pfp"
                name="pfp"
                onChange={handleFileChange}
                accept=".png,.jpg,.jpeg,.webp"
                className="file-input"
                aria-describedby={errors.pfp ? 'pfp-error' : 'pfp-help'}
                disabled={isLoading}
              />
              <label htmlFor="pfp" className="file-label">
                {formData.pfp ? formData.pfp.name : 'Escolher imagem'}
              </label>
              <span id="pfp-help" className="help-text">
                PNG, JPG, JPEG ou WEBP (máx. 5MB)
              </span>
            </div>
            {previewUrl && (
              <div className="image-preview">
                <img src={previewUrl} alt="Preview da foto de perfil" />
                <button
                  type="button"
                  onClick={handleRemoveImage}
                  className="remove-image-btn"
                  aria-label="Remover imagem"
                  disabled={isLoading}
                >
                  Remover
                </button>
              </div>
            )}
            {errors.pfp && (
              <span id="pfp-error" className="error-message" role="alert">
                {errors.pfp}
              </span>
            )}
          </div>

          {/* Botão de Submit */}
          <button type="submit" className="submit-btn" disabled={isLoading} aria-busy={isLoading}>
            {isLoading ? (
              <>
                <span className="spinner" aria-hidden="true"></span>
                Criando conta...
              </>
            ) : (
              'Criar Conta'
            )}
          </button>
        </form>

        <footer className="cadastro-footer">
          <p>
            Já tem uma conta? <a href="#login">Entrar</a>
          </p>
        </footer>
      </div>
    </div>
  );
}

export default Cadastro;
