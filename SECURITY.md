# Security Configuration Guide

## 🔒 **API Security Implementation**

### **Environment Variables Setup**

1. **Copy the example file:**
   ```bash
   copy .env.example .env
   ```

2. **Add your actual credentials to `.env`:**
   ```env
   UPSTOX_API_KEY=your_actual_api_key
   UPSTOX_API_SECRET=your_actual_secret  
   UPSTOX_ACCESS_TOKEN=your_actual_token
   ```

### **Security Features Implemented**

✅ **Environment Variables**: API keys stored in `.env` file (not in code)  
✅ **Git Ignore**: `.env` file excluded from version control  
✅ **Validation**: Checks for missing credentials on startup  
✅ **Masked Logging**: API URLs logged without sensitive parameters  
✅ **Example Template**: `.env.example` for safe sharing  

### **Security Best Practices**

1. **Never commit `.env` files** to version control
2. **Rotate API keys regularly** (especially access tokens) 
3. **Use different credentials** for development vs production
4. **Monitor API usage** for unauthorized access
5. **Implement rate limiting** to prevent abuse

### **Token Management**

- **Upstox Access Tokens expire daily** - implement refresh mechanism
- **Current token expires**: Nov 15, 2025 03:30 AM
- **Set up automated refresh** for production use

### **Production Deployment**

For production environments:
- Use secure secret management (Azure Key Vault, AWS Secrets Manager)
- Enable HTTPS only
- Implement request signing/verification
- Add API request logging and monitoring
- Use restricted API scopes where possible

## ⚠️ **Important Security Notes**

- The `.env` file contains **live trading API credentials**
- **Never share or commit** the `.env` file  
- **Regenerate keys immediately** if accidentally exposed
- **Monitor account activity** regularly for unauthorized trades