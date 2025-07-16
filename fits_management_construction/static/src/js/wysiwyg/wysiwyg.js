import { _t } from "@web/core/l10n/translation";
import { Wysiwyg } from "@web_editor/js/wysiwyg/wysiwyg";
import {
  preserveCursor,
  closestElement,
} from "@web_editor/js/editor/odoo-editor/src/OdooEditor";
import { patch } from "@web/core/utils/patch";
import { GenerateTextDialog } from "@fits_management_construction/static/src/js/wysiwyg/widget/generate_text";

patch(Wysiwyg.prototype, {
  _getPowerboxOptions() {
    const options = super._getPowerboxOptions(...arguments);
    const { commands, categories } = options;
    categories.push({
      name: _t("Google Gemini"),
      priority: 1,
    });
    commands.push({
      category: _t("Google Gemini"),
      name: _t("Generate text"),
      priority: 1,
      description: _t("Generate text"),
      fontawesome: "fa_pencil",
      callback: async () => this.openGenerateDialog(),
    });
    return { ...options, commands, categories };
  },
  async openGenerateDialog() {
    const resId = this.props.options.recordInfo.res_id;
    const resModel = this.props.options.recordInfo.res_model;
    const res = await this.env.services.orm.searchRead(resModel, [
      ["id", "=", resId],
      ["id", "name"],
    ]);
    let startPrompts = "";
    if (res[0]) {
      startPrompts = res[0].name;
    }
    const restore = preserveCursor(this.odooEditor.document);
    const params = {
      startPrompt: startPrompts,
      insert: (content) => {
        this.focus();
        restore();
        this.odooEditor.exeCommand("insert", content);
      },
    };
    this.env.services.dialog.add(GenerateTextDialog, params);
  },
});
