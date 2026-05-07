import { useEffect, useState } from "react";
import { CopyOutlined, DownloadOutlined, FormatPainterOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Modal,
  Radio,
  Segmented,
  Space,
  Spin,
  Typography,
} from "antd";

import { notify } from "@/services/notify";
import {
  type FormatResult,
  type Template,
  applyTemplate,
  listTemplates,
} from "@/services/formatting";

const { Text } = Typography;

interface FormatModalProps {
  open: boolean;
  onClose: () => void;
  /** 文章正文（markdown） */
  content: string;
  /** 文章标题（可空） */
  title?: string | null;
}

type Device = "phone" | "pc";

function FormatModal({ open, onClose, content, title }: FormatModalProps) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [templateId, setTemplateId] = useState<string>("minimal");
  const [device, setDevice] = useState<Device>("phone");
  const [loadingTpl, setLoadingTpl] = useState(false);
  const [loadingHtml, setLoadingHtml] = useState(false);
  const [result, setResult] = useState<FormatResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setLoadingTpl(true);
    listTemplates()
      .then((items) => {
        setTemplates(items);
        if (items.length && !items.find((t) => t.id === templateId)) {
          setTemplateId(items[0].id);
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : "加载模板失败"))
      .finally(() => setLoadingTpl(false));
  }, [open, templateId]);

  useEffect(() => {
    if (!open || !templateId || !content.trim()) return;
    let cancelled = false;
    setLoadingHtml(true);
    setError(null);
    applyTemplate({ template_id: templateId, title, content })
      .then((r) => {
        if (!cancelled) setResult(r);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "排版失败");
      })
      .finally(() => {
        if (!cancelled) setLoadingHtml(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, templateId, content, title]);

  const handleCopyHtml = async () => {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.html);
      notify.success("HTML 已复制，可以直接粘到微信编辑器");
    } catch {
      notify.error("复制失败，请手动选中文本");
    }
  };

  const handleDownload = async () => {
    if (!result) return;
    try {
      const full = await applyTemplate({
        template_id: templateId,
        title,
        content,
        full_page: true,
      });
      const blob = new Blob([full.html], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeTitle = (title || "article").replace(/[\\/:*?"<>|]/g, "_").slice(0, 40);
      a.download = `${safeTitle}.html`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      notify.error(e instanceof Error ? e.message : "导出失败");
    }
  };

  const previewWidth = device === "phone" ? 375 : 760;

  return (
    <Modal
      open={open}
      onCancel={onClose}
      title={
        <Space>
          <FormatPainterOutlined />
          <span>一键排版</span>
        </Space>
      }
      width={920}
      footer={[
        <Button key="copy" icon={<CopyOutlined />} disabled={!result} onClick={handleCopyHtml}>
          复制 HTML
        </Button>,
        <Button
          key="download"
          icon={<DownloadOutlined />}
          disabled={!result}
          onClick={handleDownload}
        >
          下载 .html
        </Button>,
        <Button key="close" type="primary" onClick={onClose}>
          关闭
        </Button>,
      ]}
    >
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        {error && <Alert type="error" message={error} showIcon closable />}

        <Space wrap>
          <Text>模板</Text>
          {loadingTpl ? (
            <Spin size="small" />
          ) : (
            <Radio.Group
              value={templateId}
              onChange={(e) => setTemplateId(e.target.value as string)}
              optionType="button"
              buttonStyle="solid"
              options={templates.map((t) => ({ value: t.id, label: t.name }))}
            />
          )}
          <span style={{ marginLeft: 16 }} />
          <Text>预览</Text>
          <Segmented<Device>
            value={device}
            onChange={(v) => setDevice(v as Device)}
            options={[
              { value: "phone", label: "手机" },
              { value: "pc", label: "PC" },
            ]}
          />
        </Space>

        <div
          style={{
            background: "#f5f5f5",
            padding: 24,
            borderRadius: 4,
            display: "flex",
            justifyContent: "center",
          }}
        >
          {loadingHtml ? (
            <Spin />
          ) : result ? (
            <div
              style={{
                width: previewWidth,
                background: "#fff",
                padding: 24,
                boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                maxHeight: 520,
                overflowY: "auto",
              }}
              dangerouslySetInnerHTML={{ __html: result.html }}
            />
          ) : (
            <Text type="secondary">选个模板看预览…</Text>
          )}
        </div>
      </Space>
    </Modal>
  );
}

export default FormatModal;
