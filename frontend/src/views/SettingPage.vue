<template>
  <div class="settings-page">
    <h1 class="title">设置</h1>
    
    <div class="settings-section">
      <h2 class="section-title">用户信息</h2>
      
      <div class="setting-item">
        <span class="setting-label">公司名称</span>
        <a-input v-model:value="companyName" placeholder="请输入公司名称" style="width: 300px" />
      </div>
      
      <div class="setting-item">
        <span class="setting-label">所属行业</span>
        <a-input v-model:value="industry" placeholder="请输入所属行业" style="width: 300px" />
      </div>
      
      <div class="setting-item">
        <span class="setting-label">公司地址</span>
        <a-input v-model:value="address" placeholder="请输入公司地址" style="width: 300px" />
      </div>
      
      <div class="setting-item">
        <span class="setting-label">融资轮次</span>
        <a-select v-model:value="fundingRound" style="width: 300px">
          <a-select-option value="seed">种子轮</a-select-option>
          <a-select-option value="angel">天使轮</a-select-option>
          <a-select-option value="pre-a">Pre-A轮</a-select-option>
          <a-select-option value="series-a">A轮</a-select-option>
          <a-select-option value="series-b">B轮</a-select-option>
          <a-select-option value="series-c">C轮</a-select-option>
          <a-select-option value="series-d">D轮及以上</a-select-option>
          <a-select-option value="ipo">已上市</a-select-option>
          <a-select-option value="none">暂未融资</a-select-option>
        </a-select>
      </div>
      
      <div class="setting-item">
        <span class="setting-label">经营范围</span>
        <a-textarea v-model:value="businessScope" placeholder="请输入经营范围" :rows="4" style="width: 300px" />
      </div>
      
      <div class="setting-item">
        <span class="setting-label">其他信息</span>
        <a-textarea v-model:value="otherInfo" placeholder="请输入其他信息" :rows="4" style="width: 300px" />
      </div>
      
      <div class="setting-item">
        <span class="setting-label"></span>
        <a-button type="primary" @click="saveSettings" :loading="saving">
          保存设置
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { saveUserSettings, getUserSettings } from '../api/settings';

const companyName = ref('');
const industry = ref('');
const address = ref('');
const fundingRound = ref('none');
const businessScope = ref('');
const otherInfo = ref('');
const saving = ref(false);
const loading = ref(false);

// 获取用户设置
const loadSettings = async () => {
  try {
    loading.value = true;
    const settings = await getUserSettings();
    
    if (settings) {
      companyName.value = settings.companyName || '';
      industry.value = settings.industry || '';
      address.value = settings.address || '';
      fundingRound.value = settings.fundingRound || 'none';
      businessScope.value = settings.businessScope || '';
      otherInfo.value = settings.otherInfo || '';
    }
  } catch (error) {
    console.error('获取设置失败:', error);
    // 如果是认证错误，可能需要重新登录
    if (error.response?.status === 401) {
      message.error('请先登录');
      // 可以在这里添加跳转到登录页面的逻辑
    }
    // 如果是首次访问或者没有设置，不显示错误信息
  } finally {
    loading.value = false;
  }
};

const saveSettings = async () => {
  try {
    saving.value = true;
    
    const settings = {
      companyName: companyName.value,
      industry: industry.value,
      address: address.value,
      fundingRound: fundingRound.value,
      businessScope: businessScope.value,
      otherInfo: otherInfo.value
    };
    
    await saveUserSettings(settings);
    message.success('设置保存成功');
  } catch (error) {
    console.error('保存设置失败:', error);
    if (error.response?.status === 401) {
      message.error('请先登录');
    } else if (error.response?.status === 400) {
      message.error('输入信息有误，请检查后重试');
    } else {
      message.error('保存设置失败，请重试');
    }
  } finally {
    saving.value = false;
  }
};

// 页面加载时获取设置
onMounted(() => {
  loadSettings();
});
</script>

<style scoped>
.settings-page {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.title {
  font-size: 24px;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e8e8e8;
}

.settings-section {
  margin-bottom: 30px;
}

.section-title {
  font-size: 18px;
  margin-bottom: 15px;
}

.setting-item {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.setting-label {
  width: 100px;
  font-weight: 500;
}
</style>

