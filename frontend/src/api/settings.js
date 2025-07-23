import axios from 'axios';
import { API_BASE_URL } from './config';

// 创建axios实例
const settingsApi = axios.create({
  baseURL: API_BASE_URL
});

// 请求拦截器，添加认证token
settingsApi.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 保存用户设置（公司信息）
export const saveUserSettings = async (data) => {
  try {
    // 将前端字段映射到后端字段
    const mappedData = {
      company_name: data.companyName,
      industry: data.industry,
      address: data.address,
      financing_stage: data.fundingRound,
      business_scope: data.businessScope,
      additional_info: data.otherInfo ? { other_info: data.otherInfo } : null
    };
    
    const response = await settingsApi.put('/info/company-info', mappedData);
    return response.data;
  } catch (error) {
    console.error('Failed to save user settings:', error);
    throw error;
  }
};

// 获取用户设置（从用户信息中获取公司信息）
export const getUserSettings = async () => {
  try {
    const response = await settingsApi.get('/info/me');
    const userData = response.data;
    
    // 如果有公司信息，将后端字段映射到前端字段
    if (userData.company_info) {
      const companyInfo = userData.company_info;
      return {
        companyName: companyInfo.company_name || '',
        industry: companyInfo.industry || '',
        address: companyInfo.address || '',
        fundingRound: companyInfo.financing_stage || 'none',
        businessScope: companyInfo.business_scope || '',
        otherInfo: companyInfo.additional_info?.other_info || ''
      };
    }
    
    // 如果没有公司信息，返回空对象
    return {
      companyName: '',
      industry: '',
      address: '',
      fundingRound: 'none',
      businessScope: '',
      otherInfo: ''
    };
  } catch (error) {
    console.error('Failed to get user settings:', error);
    throw error;
  }
};
